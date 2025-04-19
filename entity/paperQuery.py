import os

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from ccf_info_by_section import VENUE_TYPES
from tools.timer import Timer


class PaperQuery:

    def __init__(self, venues:list, output_dir: str = "query_result"):
        """
        初始化 PaperQuery 类
        """
        self.venues = venues
        self.output_dir = output_dir
        self.timer = Timer()  # 初始化计时器

    def get_soup(self, url):
        """
        获取指定 URL 的 BeautifulSoup 对象
        """
        try:
            res = requests.get(url, timeout=100)
            if res.status_code != 200:
                print(f"请求失败，状态码: {res.status_code}")
                return None
        except requests.RequestException as e:
            print(f"网络请求失败: {e}")
            return None
        return BeautifulSoup(res.text, 'lxml')

    def get_volume_links_journal(self, base_url:str, years:list):
        """
        提取期刊指定年份的所有卷链接
        """
        soup = self.get_soup(base_url)
        if not soup:
            print(f"⚠️ 无法获取页面内容，URL: {base_url}")
            return []

        links_by_year = {year: [] for year in years}  # 初始化按年份分类的字典

        info_section = soup.find(id="info-section")
        all_volumes = info_section.find_next_sibling("ul")
        # 遍历每个年份，找到对应的卷
        for year in years:
            year_tags = []
            for li in all_volumes.find_all("li"):
                if year in li.get_text(strip=True):
                    year_tags.append(li)

            if not year_tags:
                print(f"⚠️ 未找到年份 {year} 的卷信息")
                continue

            for year_tag in year_tags:
                volume_links = year_tag.find_all("a", href=True)
                for link in volume_links:
                    if link['href'].endswith('.html'):
                        links_by_year[year].append(link['href'])

        return links_by_year

    def get_volume_links_conference(self, base_url:str, years:list):
        """
        提取会议指定年份的所有卷链接
        """
        soup = self.get_soup(base_url)
        if not soup:
            print(f"⚠️ 无法获取页面内容，URL: {base_url}")
            return []

        links_by_year = {year: [] for year in years}  # 初始化按年份分类的字典

        div_main = soup.find(id="main")
        if not div_main:
            print(f"⚠️ 无法找到主内容区域，URL: {base_url}")
            return []

        h2_total = div_main.find_all("h2")
        if not h2_total:
            print(f"⚠️ 无法找到标题区域，URL: {base_url}")
            return []

        for year in years:
            for h2 in h2_total:
                id = h2.get('id')
                if id and year in id:
                    parent = h2.find_parent()
                    sibling = parent.find_next_sibling("ul") if parent else None
                    volume_links = sibling.find_all("a", href=True, class_="toc-link") if sibling else []
                    for link in volume_links:
                        if link['href'].endswith('.html'):
                            links_by_year[year].append(link['href'])

        return links_by_year

    def fetch_titles(self, volume_url:str):
        """
        获取文章标题（返回文章标题列表）
        """
        soup = self.get_soup(volume_url)
        if not soup:
            print(f"⚠️ 无法获取具体文章列表页内容，URL: {volume_url}")
            return []

        articles_containers = soup.find_all("ul", class_="publ-list")
        articles = []
        for container in articles_containers:
            articles.extend(container.find_all("span", class_="title"))

        if not articles:
            print(f"未找到文章标题，URL: {volume_url}")
            return []

        titles = []
        for article in articles:
            if article.get_text(strip=True).endswith(('.', '?')):
                titles.append(article.get_text(strip=True)[:-1])
            else:
                titles.append(article.get_text(strip=True))
        return titles

    def run(self, years: list, keywords: list):
        """
        主函数，处理查找所有期刊/会议的文章
        """
        output_filename = f"{'_'.join(years)}-{'_'.join([k.replace(' ', '_') for k in keywords])}.txt"
        results = []

        self.timer.start("总耗时")  # 开始总耗时计时

        for venue in self.venues:
            venue_key = venue['key']
            venue_type = venue["type"]
            venue_url = venue["url"]
            # 简称-等级-类型
            # 例如：AAAI-A-会议
            keyRankType = f"{venue_key} ({venue['rank']}类 {VENUE_TYPES.get(venue_type, '未知类型')})"

            self.timer.start(f"处理 {venue_key}")  # 开始处理单个 venue 的计时
            print(f"🔍 正在处理：{keyRankType}")

            # 根据类型动态调用对应的方法
            if venue_type == "journal":
                self.timer.start(f"获取期刊 {venue_key} 符合筛选条件的所有卷链接")
                links_by_year = self.get_volume_links_journal(venue_url, years)
                self.timer.stop(f"获取期刊 {venue_key} 符合筛选条件的所有卷链接")
            elif venue_type == "conference":
                self.timer.start(f"获取会议 {venue_key} 符合筛选条件的所有卷链接")
                links_by_year = self.get_volume_links_conference(venue_url, years)
                self.timer.stop(f"获取会议 {venue_key} 符合筛选条件的所有卷链接")
            else:
                print(f"⚠️ 未知的 venue 类型：{venue_type}")
                continue

            if len(links_by_year) == 0:
                print(f"⚠️ 没有找到符合条件的卷链接，跳过 {venue_key}")
                continue

            for year, volume_links in links_by_year.items():
                for volume_link in tqdm(volume_links, desc=f"{venue_key} ({year})"):
                    try:
                        titles = self.fetch_titles(volume_link)
                        if len(titles) == 0:
                            continue
                        for title in titles:
                            if any(keyword.lower() in title.lower() for keyword in keywords):
                                results.append(f"{year}-{keyRankType}  {title}")
                    except Exception as e:
                        print(f"[错误] 处理 {volume_link} 时失败: {e}")

            self.timer.stop(f"处理 {venue_key}\n")  # 停止处理单个 venue 的计时

        if results:
            if not os.path.exists(self.output_dir):
                os.makedirs(self.output_dir)
            output_filepath = os.path.join(self.output_dir, output_filename)
            with open(output_filepath, "w", encoding="utf-8") as f:
                f.write("\n".join(results))
            print(f"\n✅ 已保存结果到 {output_filepath}，共找到 {len(results)} 条匹配项。")
        else:
            print("\n⚠️ 没有找到匹配结果。")

        self.timer.stop("总耗时")  # 停止总耗时计时


if __name__ == "__main__":
    # 示例用法
    years = ["2025"]  # 支持多个年份查询
    keywords = [""]  # 支持多个关键词查询

    paper_query = PaperQuery()
    paper_query.run(years, keywords)