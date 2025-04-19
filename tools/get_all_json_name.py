import json
import os


def load_json_files_name(folder_path):
    """
    加载指定文件夹下的所有 JSON 文件的名字，并将其内容存储在一个列表中并输出。
    :param folder_path: 包含 JSON 文件的文件夹路径
    :return: 一个列表，包含所有 JSON 文件的名字
    """
    all_json_names = []
    for file_name in os.listdir(folder_path):
        if file_name.endswith(".json"):  # 只处理 JSON 文件
            # 不要后缀名
            file_name_without_extension = os.path.splitext(file_name)[0]
            all_json_names.append(file_name_without_extension)
    return all_json_names

if __name__ == "__main__":
    # 示例用法
    folder_path = os.path.join(os.path.dirname(__file__), "../ccf_info_by_section")  # 根据相对路径定位到ccf_info_by_section
    # print(f"当前路径: {folder_path}")
    all_json_names = load_json_files_name(folder_path)
    print(all_json_names)
