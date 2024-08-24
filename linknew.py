import base64
import json
import geoip2.database
import socket
import os
import urllib.request
from urllib.parse import urlparse

def download_geoip_db(db_path, repo="maxmind/GeoLite2-Country", target="GeoLite2-Country.mmdb"):
    """Download GeoLite2-Country.mmdb from GitHub release."""
    if os.path.exists(db_path):
        print(f"GeoIP database already exists at {db_path}.")
        return db_path
    
    # GitHub API URL to fetch the latest release
    release_api = f"https://api.github.com/repos/{repo}/releases/latest"
    try:
        with urllib.request.urlopen(release_api) as response:
            data = json.loads(response.read().decode())
            assets = data.get("assets", [])
            download_url = next((asset["browser_download_url"] for asset in assets if asset["name"] == target), None)
            if not download_url:
                print(f"Could not find {target} in the latest GitHub release.")
                return None
            
            # Download the file
            print(f"Downloading {target} from {download_url}...")
            urllib.request.urlretrieve(download_url, db_path)
            print(f"Downloaded GeoIP database to {db_path}.")
    except Exception as e:
        print(f"Failed to download GeoIP database: {e}")
        return None
    
    return db_path

def decode_vmess(vmess_link):
    """Decode vmess link from Base64."""
    encoded_data = vmess_link[len("vmess://"):]
    decoded_data = base64.urlsafe_b64decode(encoded_data + '=' * (4 - len(encoded_data) % 4)).decode('utf-8')
    return json.loads(decoded_data)

def parse_vless(vless_link):
    """Parse vless link and extract relevant fields."""
    parsed_url = urlparse(vless_link)
    return {
        "ps": parsed_url.hostname,
        "add": parsed_url.hostname,
        "port": parsed_url.port,
        "id": parsed_url.username,
        "path": parsed_url.path,
        "type": parsed_url.query.split('=')[1] if 'type' in parsed_url.query else "none"
    }

def rename_ps_by_geoip(proxy, reader, country_counts):
    """Rename the 'ps' field using geoip2 to get country name and handle duplicates."""
    try:
        ip = socket.gethostbyname(proxy['add'])
        response = reader.country(ip)
        country_name = response.country.names.get("zh-CN", "未知国家")
        
        # If the country name has been used, add a number suffix
        if country_name in country_counts:
            country_counts[country_name] += 1
            proxy['ps'] = f"{country_name}-{country_counts[country_name]}"
        else:
            country_counts[country_name] = 1
            proxy['ps'] = country_name
    except Exception as e:
        print(f"Error occurred: {e}")
        proxy['ps'] = "未知国家"
    return proxy

def encode_vmess(proxy):
    """Encode vmess proxy dict to a vmess link."""
    json_data = json.dumps(proxy)
    encoded_data = base64.urlsafe_b64encode(json_data.encode('utf-8')).decode('utf-8')
    return f"vmess://{encoded_data}"

def format_vless(proxy):
    """Format vless proxy dict to a vless link."""
    return f"vless://{proxy['id']}@{proxy['add']}:{proxy['port']}?type={proxy['type']}&path={proxy['path']}"

def process_vmess_links(vmess_links, reader, country_counts):
    """Process a list of vmess links and rename their 'ps' fields."""
    processed_links = []
    for link in vmess_links:
        proxy = decode_vmess(link)
        proxy = rename_ps_by_geoip(proxy, reader, country_counts)
        processed_links.append(encode_vmess(proxy))
    return processed_links

def process_vless_links(vless_links, reader, country_counts):
    """Process a list of vless links and rename their 'ps' fields."""
    processed_links = []
    for link in vless_links:
        proxy = parse_vless(link)
        proxy = rename_ps_by_geoip(proxy, reader, country_counts)
        processed_links.append(format_vless(proxy))
    return processed_links

def read_links(file_path):
    """Read links from a file."""
    with open(file_path, 'r') as file:
        links = file.read().splitlines()
    return links

def write_links(file_path, links):
    """Write links to a file."""
    with open(file_path, 'w') as file:
        for link in links:
            file.write(f"{link}\n")

# 主程序
def main():
    input_file = 'link.txt'
    output_file = 'link-new.txt'
    db_directory = './geoip_db'
    db_file = 'GeoLite2-Country.mmdb'
    db_path = os.path.join(db_directory, db_file)

    if not os.path.exists(db_directory):
        os.makedirs(db_directory)

    # 下载 GeoIP2 数据库
    db_path = download_geoip_db(db_path)

    if not db_path or not os.path.exists(db_path):
        print("GeoIP2 数据库下载失败或文件不存在。")
        return

    # 加载 GeoIP2 数据库
    reader = geoip2.database.Reader(db_path)

    # 从文件中读取链接
    links = read_links(input_file)

    # 初始化国家计数器
    country_counts = {}

    # 分别处理 vmess 和 vless 链接
    vmess_links = [link for link in links if link.startswith("vmess://")]
    vless_links = [link for link in links if link.startswith("vless://")]

    processed_vmess = process_vmess_links(vmess_links, reader, country_counts)
    processed_vless = process_vless_links(vless_links, reader, country_counts)

    # 写入处理后的链接到新文件
    write_links(output_file, processed_vmess + processed_vless)

    print(f"Processed links have been written to {output_file}")

if __name__ == "__main__":
    main()
