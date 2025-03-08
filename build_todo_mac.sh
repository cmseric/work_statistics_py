#!/bin/bash

# 进入当前脚本所在的目录
cd "$(dirname "$0")"

# 激活虚拟环境
source venv/bin/activate

# 清空 dist 文件夹
if [ -d "dist" ]; then
    rm -rf dist/*
else
    mkdir dist
fi

# 生成macOS应用包
python build_todo.py

# 删除旧的 DMG 文件，避免冲突
rm -f "TodoTracker-1.0.dmg"

# 创建 DMG 安装包
create-dmg \
  --volname "TodoTracker Installer" \
  --window-pos 200 120 \
  --window-size 800 400 \
  --icon-size 100 \
  --icon "TodoTracker.app" 200 190 \
  --app-drop-link 600 190 \
  --no-internet-enable \
  --skip-jenkins \
  "dist/TodoTracker-1.0.dmg" \
  "dist/"

# 可选：运行完毕后退出虚拟环境
deactivate