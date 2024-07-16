import json

# 读取 JSON 文件
with open("./output.json", "r", encoding="utf-8") as file:
    data = json.load(file)

# 函数：提取并筛选订阅链接
def extract_and_filter_links(json_data):
    links = []
    for item in json_data:
        for link in item.get("link", []):
            if not (link.startswith("http") or "sock" in link or link.startswith("ss://")):
                links.append(link)
    return links

# 提取并筛选订阅链接
links = extract_and_filter_links(data)

# 输出到文本文件
with open("link.txt", "w", encoding="utf-8") as f:
    for link in links:
        f.write(link + "\n")
