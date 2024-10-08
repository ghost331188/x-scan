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

# 函数：将 JSON 转换为 Markdown 表格
def json_to_markdown(json_data):
    headers = [
        "xray状态",
        "xray版本",
        "运行时间",
        "上行总流量",
        "下行总流量",
        "订阅链接",
    ]
    markdown_table = "| " + " | ".join(headers) + " |\n"
    markdown_table += "| " + " | ".join(["---"] * len(headers)) + " |\n"

    for item in json_data:
        xrayState = item.get("xrayState", "")
        xrayVersion = item.get("xrayVersion", "")
        uptime = item.get("uptime", "")
        sent = item.get("sent", "")
        recv = item.get("recv", "")
        link = "<br />".join(item.get("link", []))

        markdown_table += (
            f"| {xrayState} | {xrayVersion} | {uptime} | {sent} | {recv} | {link} |\n"
        )

    return markdown_table

# 提取并筛选订阅链接
links = extract_and_filter_links(data)

# 输出筛选后的链接到文本文件
with open("link.txt", "w", encoding="utf-8") as f:
    for link in links:
        f.write(link + "\n")

# 将 JSON 数据转换为 Markdown 表格
markdown_table = json_to_markdown(data)

# 输出 Markdown 表格到文件
with open("check.md", "w", encoding="utf-8") as f:
    f.write(markdown_table)
