#!/bin/bash

# 检查端口是否被占用
if lsof -ti:5010 > /dev/null; then
    echo "端口5010已被占用，正在尝试释放..."
    ./stop_api.sh
    sleep 1
fi

cd ../
# 激活虚拟环境
source venv/bin/activate
cd ./todo_kpi_v1

# 启动API服务
python api_server.py

# 如果服务异常退出，等待用户确认
if [ $? -ne 0 ]; then
    echo "API服务异常退出，错误代码：$?"
    read -p "按回车键继续..."
fi

# 退出虚拟环境
deactivate 