#!/bin/bash

#pip install pandas tqdm requests

#筛选
python fofa-xui.py

# 提取节点
python collect.py

# 导出节点连接link.txt和check.md
python json-out.py

echo "done"

