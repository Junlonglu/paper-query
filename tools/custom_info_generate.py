import json
import os

# 全部目标板块（section
all_sections = [
  'artificial_intelligence', 
  'computer_architecture', 
  'computer_graphics_and_multimedia', 
  'computer_networks', 
  'computer_science_theory', 
  'cross_interdisciplinary_and_emerging', 
  'databases_and_data_mining', 
  'human_computer_interaction', 
  'network_and_information_security', 
  'software_engineering'
]

# 每个板块里的内容构成：
section_structure = ['journal_A', 'journal_B', 'journal_C','conference_A', 'conference_B', 'conference_C']

def extract_custom_info(json_dir, output_path, import_config):
    """
    从指定路径根据配置提取期刊/会议信息并输出合并文件

    参数：
    - json_dir: JSON 文件目录（每个 section 一个文件）
    - output_path: 最终合并输出的 JSON 文件路径
    - import_config: dict，结构为 {section_name: [key1, key2, ...]}

    返回：
    - 提取出的记录总数
    """
    all_results = []

    for section, keys in import_config.items():
        filename = f"{section}.json"
        file_path = os.path.join(json_dir, filename)

        if not os.path.exists(file_path):
            print(f"⚠️ 找不到文件：{filename}")
            continue

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            for key in keys:
                if key in data:
                    all_results.extend(data[key])

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    print(f"✅ 导入完成，共 {len(all_results)} 条记录 -> {output_path}")
    return len(all_results)

if __name__ == "__main__":
    json_dir = os.path.join(os.path.dirname(__file__), "../ccf_info_by_section") # 加载 JSON 文件的目录
    output_file = os.path.join(os.path.dirname(__file__), "../custom_info/default.json") # 输出文件路径

    import_config = {
        "artificial_intelligence": ["journal_A", "journal_B", "conference_A", "conference_B"],
        "databases_and_data_mining": ["journal_A", "journal_B", "conference_A", "conference_B"],
    }

    extract_custom_info(json_dir, output_file, import_config)


