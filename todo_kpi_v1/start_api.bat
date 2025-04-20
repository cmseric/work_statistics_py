@echo off
setlocal enabledelayedexpansion

:: 检查端口是否被占用
netstat -ano | findstr :5010 > nul
if %errorlevel% equ 0 (
    echo 端口5010已被占用，正在尝试释放...
    call stop_api.bat
    timeout /t 2 /nobreak > nul
)

:: 激活虚拟环境
call venv\Scripts\activate.bat

:: 启动API服务
python api_server.py

:: 如果服务异常退出，等待用户确认
if %errorlevel% neq 0 (
    echo API服务异常退出，错误代码：%errorlevel%
    pause
)

:: 退出虚拟环境
call venv\Scripts\deactivate.bat 