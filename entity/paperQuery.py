import logging
import multiprocessing
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from io import StringIO

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from ccf_info_by_section import VENUE_TYPES
from tools.logger_utils import setup_logger
from tools.timer import Timer


class PaperQuery:
    def __init__(self, venues: list):
        self.venues = venues
        
        self.timer = Timer()

    def get_soup(self, url: str, local_logger=None):
        try:
            res = requests.get(url, timeout=1000)
            if res.status_code != 200:
                local_logger.warning(f"请求失败，状态码: {res.status_code}，URL: {url}")
                return None
        except requests.RequestException as e:
            local_logger.error(f"网络请求失败: {e}，URL: {url}")
            return None
        return BeautifulSoup(res.text, 'lxml')

    def get_volume_links_journal(self, base_url: str, years: list, local_logger=None):
        soup = self.get_soup(base_url, local_logger)
        if not soup:
            local_logger.warning(f"⚠️ 无法获取页面内容，URL: {base_url}")
            return []

        links_by_year = {year: [] for year in years}
        info_section = soup.find(id="info-section")
        all_volumes = info_section.find_next_sibling("ul")

        for year in years:
            year_tags = [li for li in all_volumes.find_all("li") if year in li.get_text(strip=True)]
            if not year_tags:
                local_logger.warning(f"⚠️ 未找到年份 {year} 的卷信息")
                continue

            for year_tag in year_tags:
                for link in year_tag.find_all("a", href=True):
                    if link['href'].endswith('.html'):
                        links_by_year[year].append(link['href'])

        return links_by_year

    def get_volume_links_conference(self, base_url: str, years: list, local_logger=None):
        soup = self.get_soup(base_url, local_logger)
        if not soup:
            local_logger.warning(f"⚠️ 无法获取页面内容，URL: {base_url}")
            return []

        links_by_year = {year: [] for year in years}
        div_main = soup.find(id="main")
        if not div_main:
            local_logger.warning(f"⚠️ 无法找到主内容区域，URL: {base_url}")
            return []

        h2_total = div_main.find_all("h2")
        for year in years:
            for h2 in h2_total:
                id = h2.get('id')
                if id and year in id:
                    sibling = h2.find_parent().find_next_sibling("ul")
                    volume_links = sibling.find_all("a", href=True, class_="toc-link") if sibling else []
                    for link in volume_links:
                        if link['href'].endswith('.html'):
                            links_by_year[year].append(link['href'])

        return links_by_year

    def fetch_titles(self, volume_url: str, local_logger=None):
        soup = self.get_soup(volume_url, local_logger)
        if not soup:
            local_logger.warning(f"⚠️ 无法获取具体文章列表页内容，URL: {volume_url}")
            return []

        articles = []
        for container in soup.find_all("ul", class_="publ-list"):
            articles.extend(container.find_all("span", class_="title"))

        if not articles:
            local_logger.warning(f"⚠️ 未找到文章标题，URL: {volume_url}")
            return []

        titles = []
        for article in articles:
            text = article.get_text(strip=True)
            if text.endswith(('.', '?')):
                text = text[:-1]
            titles.append(text)
        return titles

    def get_recommended_thread_count(self, task_type="io"):
        cpu_count = multiprocessing.cpu_count()
        return cpu_count * 5 if task_type.lower() == "io" else cpu_count

    def process_venue(self, venue: dict, years: list, keywords: list):

        results = []

        venue_key = venue['key']
        venue_type = venue['type']
        venue_url = venue['url']
        key_rank_type = f"{venue_key} ({venue['rank']}类 {VENUE_TYPES.get(venue_type, '未知类型')})"

        buffer = StringIO()
        local_logger = logging.getLogger(f"local_{venue['key']}")
        local_logger.setLevel(logging.INFO)

        # 仅为本地 logger 添加临时 handler（内存中）
        buffer_handler = logging.StreamHandler(buffer)
        formatter = logging.Formatter(fmt='%(thread)d - %(asctime)s - %(filename)s[line:%(lineno)d] - %(funcName)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S %p')
        buffer_handler.setFormatter(formatter)
        local_logger.addHandler(buffer_handler)

        local_logger.info(f"🔍 开始处理：{key_rank_type}")

        if venue_type == "journal":
            links_by_year = self.get_volume_links_journal(venue_url, years, local_logger)
        elif venue_type == "conference":
            links_by_year = self.get_volume_links_conference(venue_url, years, local_logger)
        else:
            local_logger.warning(f"⚠️ 未知类型：{venue_type}，跳过 {venue_key}")
            return []

        if not links_by_year:
            local_logger.warning(f"⚠️ 没有找到符合条件的卷链接，跳过 {venue_key}")
            return []

        for year, volume_links in links_by_year.items():
            for volume_link in volume_links:
                titles = self.fetch_titles(volume_link, local_logger)
                if not titles:
                    local_logger.warning(f"⚠️ 未找到文章标题，跳过 {volume_link}")
                    continue
                for title in titles:
                    if any(keyword.lower() in title.lower() for keyword in keywords):
                        results.append(f"{year}-@-{key_rank_type}-@-{title}")

        local_logger.info(f"🎯 完成：{key_rank_type}，共找到 {len(results)} 条匹配项。")

        # 手动将 buffer 内容写入主 logger，并清除 handler
        log_content = buffer.getvalue()
        self.logger.info(f"\n========== 日志分组：{key_rank_type} ==========\n{log_content}\n")

        buffer_handler.close()
        local_logger.removeHandler(buffer_handler)
        buffer.close()

        return results

    def run(self, years: list, keywords: list, output_dir: str = "query_result"):

        self.output_dir = output_dir # 输出目录
        self.output_logs_dir = os.path.join(output_dir, "logs") # 日志目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{'-'.join(years)}-{'_'.join([k.replace(' ', '_') for k in keywords])}({timestamp}).txt"
        output_path = os.path.join(self.output_dir, output_filename)

        self.logger = setup_logger("PaperQueryLogger", os.path.join(self.output_logs_dir, output_filename.replace('.txt', '.log')))

        all_results = []

        self.timer.start("总耗时")

        with ThreadPoolExecutor(max_workers=self.get_recommended_thread_count("io")) as executor:
            futures = [executor.submit(self.process_venue, venue, years, keywords) for venue in self.venues]
            for future in tqdm(as_completed(futures), total=len(self.venues), desc="整体进度"):
                results = future.result()
                all_results.extend(results)

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(all_results))
        self.logger.info(f"✅ 已保存结果到 {output_path}，共找到 {len(all_results)} 条匹配项。")

        elapsed_time = self.timer.stop("总耗时")
        self.logger.info(f"⏱️ 总耗时: {elapsed_time:.2f} 秒")




if __name__ == "__main__":
    # 示例用法
    years = ["2025"]  # 支持多个年份查询
    keywords = [""]  # 支持多个关键词查询

    paper_query = PaperQuery()
    paper_query.run(years, keywords)