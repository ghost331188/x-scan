import base64
import json
import geoip2.database
import socket
import os
from urllib.parse import urlparse, parse_qs, unquote

# 读取 JSON 文件并提取、筛选订阅链接
def extract_and_filter_links(json_file):
    with open(json_file, "r", encoding="utf-8") as file:
        data = json.load(file)
    links = []
    for item in data:
        for link in item.get("link", []):
            if link.startswith("vmess://") or link.startswith("vless://"):
                links.append(link)
    return links

# 解析并解码 vmess 链接
def decode_vmess(vmess_link):
    encoded_data = vmess_link[len("vmess://"):]
    decoded_data = base64.urlsafe_b64decode(encoded_data + '=' * (4 - len(encoded_data) % 4)).decode('utf-8')
    return json.loads(decoded_data)

# 解析 vless 链接
def parse_vless(vless_link):
    parsed_url = urlparse(vless_link)
    query = parse_qs(parsed_url.query)
    return {
        "id": parsed_url.username,
        "add": parsed_url.hostname,
        "port": parsed_url.port or "443",
        "path": unquote(query.get("path", ["/"])[0]),
        "type": query.get("type", ["ws"])[0],
        "security": query.get("security", ["none"])[0],
        "encryption": query.get("encryption", ["none"])[0],
        "flow": query.get("flow", [""])[0],
        "ps": parsed_url.fragment or "未知国家"  # 备注部分，国家信息
    }

# 根据 GeoIP 数据库重命名 'ps' 字段，并处理重名情况
def rename_ps_by_geoip(proxy, reader, country_counts):
    try:
        if proxy['add']:  # 确保地址存在
            ip = socket.gethostbyname(proxy['add'])
            response = reader.country(ip)
            country_name = response.country.names.get("zh-CN", "未知国家")

            if country_name in country_counts:
                country_counts[country_name] += 1
                proxy['ps'] = f"{country_name}-{country_counts[country_name]}"
            else:
                country_counts[country_name] = 1
                proxy['ps'] = country_name
        else:
            proxy['ps'] = proxy.get('ps', '未知服务器')
    except (socket.gaierror, socket.error) as e:
        print(f"DNS解析错误: {e}")
        proxy['ps'] = proxy.get('ps', '未知服务器')
    except geoip2.errors.AddressNotFoundError:
        print("无法在GeoIP数据库中找到该IP地址")
        proxy['ps'] = proxy.get('ps', '未知国家')
    except Exception as e:
        print(f"未知错误: {e}")
        proxy['ps'] = proxy.get('ps', '未知服务器')
    return proxy

# 编码 vmess 链接
def encode_vmess(proxy):
    json_data = json.dumps(proxy)
    encoded_data = base64.urlsafe_b64encode(json_data.encode('utf-8')).decode('utf-8')
    return f"vmess://{encoded_data}"

# 格式化 vless 链接
def format_vless(proxy):
    query = (
        f"path={proxy['path']}&security={proxy['security']}&"
        f"encryption={proxy['encryption']}&type={proxy['type']}&"
        f"flow={proxy['flow']}"
    )
    return (
        f"vless://{proxy['id']}@{proxy['add']}:{proxy['port']}?"
        f"{query}#{proxy['ps']}"
    )

# 处理并格式化 vmess 和 vless 链接
def process_links(links, reader, country_counts):
    processed_links = []
    for link in links:
        if link.startswith("vmess://"):
            proxy = decode_vmess(link)
            proxy = rename_ps_by_geoip(proxy, reader, country_counts)
            processed_links.append(encode_vmess(proxy))
        elif link.startswith("vless://"):
            proxy = parse_vless(link)
            proxy = rename_ps_by_geoip(proxy, reader, country_counts)
            processed_links.append(format_vless(proxy))
    return processed_links

# 写入处理后的链接到文件
def write_links(file_path, links):
    with open(file_path, 'w', encoding='utf-8') as file:
        for link in links:
            file.write(f"{link}\n")

# 主程序
def main():
    json_file = 'output.json'
    output_file = 'link-new.txt'
    db_file = './geoip_db/GeoLite2-Country.mmdb'

    if not os.path.exists(db_file):
        print("GeoIP2 数据库不存在。")
        return

    reader = geoip2.database.Reader(db_file)
    links = extract_and_filter_links(json_file)
    country_counts = {}
    processed_links = process_links(links, reader, country_counts)
    write_links(output_file, processed_links)

    print(f"处理后的链接已写入 {output_file}")

if __name__ == "__main__":
    main()
