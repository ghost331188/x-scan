import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor
import logging
import base64

# 设置日志记录
logging.basicConfig(filename='host_check.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# 读取 notls.csv 和 tls.csv 文件中的链接
df_notls = pd.read_csv('notls.csv')  # 假设你的 CSV 文件名为 notls.csv
df_tls = pd.read_csv('tls.csv')  # 假设你的 CSV 文件名为 tls.csv

# 获取所有链接列表
link_list = df_notls['link'].tolist() + df_tls['link'].tolist()  # 假设链接列的名称为 'link'

def check_host(link):
    try:
        sub_url = f'{link}/sub/89b3cbba-e6ac-485a-9481-976a0415eab9'
        headers = {
            'authority': 'vpn.leertai.top',
            'accept': '*/*',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'zh-CN,zh;q=0.9',
            'origin': 'https://vpn.leertai.top',
            'referer': 'https://vpn.leertai.top/login',
            'sec-ch-ua': '"Google Chrome";v="111", "Not(A:Brand";v="8", "Chromium";v="111"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36'
        }
        
        # 发送 sub 请求
        sub_response = requests.get(sub_url, headers=headers, timeout=1)
        if sub_response.status_code == 200:
            logging.info(f'Successful sub request: {link}')
            decoded_content = base64.b64decode(sub_response.text).decode('utf-8')
            with open('bqb.txt', 'a', encoding='utf-8') as f:
                f.write(f'{decoded_content}\n')
            print(f'成功解码并写入文件的内容: {decoded_content}')
        else:
            logging.info(f'请求失败: {link} (状态码: {sub_response.status_code})')
            print(f'请求失败: {link} (状态码: {sub_response.status_code})')
    except requests.exceptions.Timeout:
        logging.error(f'{link} 请求超时')
        print(f'请求超时: {link}')
    except requests.exceptions.RequestException as e:
        logging.error(f'{link} 连接错误: {e}')
        print(f'连接错误: {link}，错误信息: {e}')

# 使用 ThreadPoolExecutor 进行多线程处理
with ThreadPoolExecutor(max_workers=100) as executor:
    executor.map(check_host, link_list)
