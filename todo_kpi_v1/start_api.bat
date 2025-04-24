@echo off
setlocal enabledelayedexpansion

:: 获取脚本所在目录
set "SCRIPT_DIR=%~dp0"
set "ROOT_DIR=%~dp0..\"

:: 检查端口是否被占用
netstat -ano | findstr :5010 > nul
if %errorlevel% equ 0 (
    echo 端口5010已被占用，正在尝试释放...
    call "%SCRIPT_DIR%stop_api.bat"
    timeout /t 2 /nobreak > nul
)

:: 激活虚拟环境（从根目录）
call "%ROOT_DIR%venv\Scripts\activate.bat"

:: 设置环境变量
set PYTHONPATH=%ROOT_DIR%
set FLASK_APP=%SCRIPT_DIR%api_server.py
set FLASK_ENV=development

:: 启动API服务
cd /d "%SCRIPT_DIR%"
python -c "from dotenv import load_dotenv; load_dotenv('%ROOT_DIR%.env'); import api_server"
python api_server.py

:: 如果服务异常退出，等待用户确认
if %errorlevel% neq 0 (
    echo API服务异常退出，错误代码：%errorlevel%
    pause
)

:: 退出虚拟环境
call "%ROOT_DIR%venv\Scripts\deactivate.bat" 