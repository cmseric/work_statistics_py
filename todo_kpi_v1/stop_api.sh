#!/bin/bash

echo "正在查找占用5010端口的进程..."

# 查找占用5010端口的进程ID
PID=$(lsof -ti:5010)

if [ ! -z "$PID" ]; then
    echo "找到进程ID: $PID"
    # 终止进程
    kill -9 $PID
    echo "已终止进程"
else
    echo "未找到占用5010端口的进程"
fi

echo "端口5010已释放" 