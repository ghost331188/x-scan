#!/bin/bash

#筛选
python fofa-xui.py

# 提取节点
python collect.py

# 导出节点连接link.txt
python json-to-link.py

#导出节点信息md
python json-to-md.py

echo "done"

