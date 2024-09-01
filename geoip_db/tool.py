import requests
import json
import base64
import urllib.parse
import re
import geoip2.database
from concurrent.futures import ThreadPoolExecutor, as_completed
import random
import string

geoip_database_path = "./GeoLite2-Country.mmdb"
ip_file_path = "./ip.txt"
output_file_path = "./link.json"
links_output_file_path = "./links.txt"  # 保存生成的所有链接

def get_country_from_ip(ip_address):
    """获取IP地址的国家信息，优先显示中文名称"""
    try:
        with geoip2.database.Reader(geoip_database_path) as reader:
            response = reader.country(ip_address)
            country_name = response.country.names.get('zh-CN', ip_address)
            return country_name
    except Exception:
        return ip_address  # 如果出现异常，返回IP地址本身

def generate_random_suffix():
    """生成一个字母在前和一个编号（0-100）在后的后缀"""
    random_letter = random.choice(string.ascii_uppercase)  # 选择一个大写字母
    random_number = random.randint(0, 100)  # 选择0到100之间的一个数字
    return f"{random_letter}{random_number}"

def generate_subscription_links(data, ip_address):
    """生成订阅链接"""
    links = []
    country = get_country_from_ip(ip_address)

    if data["success"]:
        for item in data["obj"]:
            if item["enable"]:
                # 为每个链接生成一个随机后缀
                country_suffix = generate_random_suffix()
                country_with_suffix = f"{country}-{country_suffix}"  # 使用国家名称和随机编号

                protocol = item["protocol"]
                port = item["port"]
                link = ""
                if protocol == "vless":
                    settings = json.loads(item["settings"])
                    client_id = settings["clients"][0]["id"]
                    flow = settings["clients"][0].get("flow", "")
                    stream_settings = json.loads(item["streamSettings"])
                    network = stream_settings["network"]
                    security = stream_settings["security"]
                    ws_settings = stream_settings.get("wsSettings", {})
                    path = ws_settings.get("path", "/")
                    query = f"type={network}&security={security}&path={urllib.parse.quote(path)}"
                    if flow:
                        query += f"&flow={flow}"
                    # 添加国家和编号到末尾
                    link = f"{protocol}://{client_id}@{ip_address}:{port}?{query}#{country_with_suffix}"
                elif protocol == "vmess":
                    settings = json.loads(item["settings"])
                    client_id = settings["clients"][0]["id"]
                    stream_settings = json.loads(item["streamSettings"])
                    network = stream_settings["network"]
                    ws_settings = stream_settings.get("wsSettings", {})
                    path = ws_settings.get("path", "/")
                    vmess_config = {
                        "v": "2",
                        "ps": country_with_suffix,
                        "add": ip_address,
                        "port": item["port"],
                        "id": client_id,
                        "aid": "0",
                        "net": network,
                        "type": "none",
                        "host": "",
                        "path": path,
                        "tls": "",
                    }
                    link = f"vmess://{base64.urlsafe_b64encode(json.dumps(vmess_config).encode()).decode().strip('=')}"
                elif protocol == "trojan":
                    settings = json.loads(item["settings"])
                    client_id = settings["clients"][0]["password"]
                    query = "type=tcp&security=tls"  # 假设 Trojran 协议默认的查询参数
                    # 添加国家和编号到末尾
                    link = f"trojan://{client_id}@{ip_address}:{port}/?{query}#{country_with_suffix}"
                elif protocol == "shadowsocks":
                    settings = json.loads(item["settings"])
                    method = settings["method"]
                    password = settings["password"]
                    # 添加国家和编号到末尾
                    link = f"ss://{base64.urlsafe_b64encode(f'{method}:{password}@{ip_address}:{port}'.encode()).decode().strip('=')}#{country_with_suffix}"
                elif protocol == "http":
                    settings = json.loads(item["settings"])
                    user = settings["accounts"][0]["user"]
                    password = settings["accounts"][0]["pass"]
                    # 拼接国家名称和随机后缀
                    link = f"{protocol}://{user}:{password}@{ip_address}:{port}/#{country_with_suffix}"
                elif protocol == "socks":
                    settings = json.loads(item["settings"])
                    user = settings["accounts"][0]["user"]
                    password = settings["accounts"][0]["pass"]
                    # 拼接国家名称和随机后缀
                    link = f"{protocol}://{user}:{password}@{ip_address}:{port}/#{country_with_suffix}"

                links.append(link)

    return links, ip_address, country_with_suffix

def getSession(url):
    """获取会话 cookie"""
    data = {"username": "admin", "password": "admin"}
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    }

    try:
        response = requests.post(url + "/login", data=data, headers=headers, timeout=5)  # 设置超时时间为5秒
        response.raise_for_status()
        cookies = response.cookies
        session_cookie = cookies.get("session")
        return session_cookie
    except (requests.exceptions.RequestException, requests.exceptions.Timeout):
        return None

def get_inbound_list(url, session_cookie):
    """获取节点列表"""
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Cookie": f"session={session_cookie}",
    }
    try:
        response = requests.post(url + "/xui/inbound/list", headers=headers, timeout=5)  # 设置超时时间为5秒
        response.raise_for_status()
        inbound_list = response.json()
        return inbound_list
    except (requests.exceptions.RequestException, requests.exceptions.Timeout):
        return None

def extract_ip_from_url(url):
    """从 URL 中提取 IP 地址"""
    ip_pattern = r"(?:http:\/\/|https:\/\/)?(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
    match = re.search(ip_pattern, url)
    if match:
        return match.group(1)
    return None

def read_urls_from_file(file_path):
    """从文件中读取URL列表"""
    try:
        with open(file_path, "r") as file:
            urls = [line.strip() for line in file if line.strip()]
        return urls
    except FileNotFoundError:
        return []

def process_url(url):
    """处理单个 URL，获取订阅链接信息"""
    session = getSession(url)
    if not session:
        return None  # 如果请求超时或出错，直接放弃

    inbound_list = get_inbound_list(url, session)
    if not inbound_list:
        return None  # 如果请求超时或出错，直接放弃

    ip_address = extract_ip_from_url(url)
    if ip_address:
        links, ip, country = generate_subscription_links(inbound_list, ip_address)
        return {
            "url": url,  # 添加 url 字段
            "links": links,
            "ip": ip,
            "country": country
        }
    return None

def classify_links(links):
    """按协议类型分类链接"""
    vmess_links = []
    vless_links = []
    trojan_links = []
    ss_links = []
    http_links = []
    socks_links = []

    for link in links:
        if link.startswith("vmess://"):
            vmess_links.append(link)
        elif link.startswith("vless://"):
            vless_links.append(link)
        elif link.startswith("trojan://"):
            trojan_links.append(link)
        elif link.startswith("ss://"):
            ss_links.append(link)
        elif link.startswith("http://"):
            http_links.append(link)
        elif link.startswith("socks://"):
            socks_links.append(link)
    
    return vmess_links, vless_links, trojan_links, ss_links, http_links, socks_links

# 主函数
if __name__ == "__main__":
    urls = read_urls_from_file(ip_file_path)
    results = []

    # 使用线程池并发处理 URL
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = {executor.submit(process_url, url): url for url in urls}
        for future in as_completed(future_to_url):
            result = future.result()
            if result:
                results.append(result)

    # 将所有链接写入 links.txt 文件
    all_links = []
    with open(links_output_file_path, "w") as links_file:
        for result in results:
            for link in result['links']:
                if link:  # 仅写入非空链接
                    links_file.write(link + "\n")
                    all_links.append(link)

    # 从 links.txt 读取链接并分类
    with open(links_output_file_path, "r") as file:
        all_links = file.readlines()

    # 分类链接
    vmess_links, vless_links, trojan_links, ss_links, http_links, socks_links = classify_links(all_links)

    # 将分类后的链接写回 links.txt 文件
    with open(links_output_file_path, "w") as links_file:
        links_file.write("\n")
        links_file.writelines(vmess_links)
        links_file.write("\n")
        links_file.writelines(vless_links)
        links_file.write("\n")
        links_file.writelines(trojan_links)
        links_file.write("\n")
        links_file.writelines(ss_links)
        links_file.write("\n")
        links_file.writelines(http_links)
        links_file.write("\n")
        links_file.writelines(socks_links)
