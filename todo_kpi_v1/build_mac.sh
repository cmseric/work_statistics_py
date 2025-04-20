#!/bin/bash

# 激活虚拟环境
source venv/bin/activate

cd "$(dirname "$0")"

# 从main.py中获取版本号，排除注释部分
VERSION=$(grep "VERSION = " main.py | sed 's/#.*$//' | cut -d'"' -f2 | tr -d ' ')

echo "当前版本号: $VERSION"

# 清空 dist 文件夹
if [ -d "dist" ]; then
    rm -rf dist/*
else
    mkdir dist
fi

# 生成macOS应用包
python build.py

# 检查应用是否生成成功
APP_PATH="dist/TodoTracker.app"
if [ ! -d "$APP_PATH" ]; then
    echo "错误: 应用包未生成成功"
    exit 1
fi

echo "应用包生成成功: $APP_PATH"

# 删除旧的 DMG 文件，避免冲突
DMG_PATH="dist/TodoTracker_release_${VERSION}.dmg"
if [ -f "$DMG_PATH" ]; then
    rm -f "$DMG_PATH"
fi

# 创建 DMG 安装包
echo "开始创建 DMG 安装包..."
create-dmg \
  --volname "TodoTracker ${VERSION} Installer" \
  --icon-size 100 \
  --icon "TodoTracker_release_${VERSION}.app" 200 190 \
  --app-drop-link 600 190 \
  --no-internet-enable \
  --skip-jenkins \
  "$DMG_PATH" \
  "$APP_PATH"

# 检查 DMG 是否创建成功
if [ ! -f "$DMG_PATH" ]; then
    echo "错误: DMG 文件未生成成功"
    exit 1
fi

echo "DMG 安装包创建成功: $DMG_PATH"

# 退出虚拟环境
deactivate