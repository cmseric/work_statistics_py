@echo off
setlocal enabledelayedexpansion

:: 进入当前脚本所在的目录
cd /d "%~dp0"
cd ..

:: 激活虚拟环境
call venv\Scripts\activate.bat

cd /d "%~dp0"

:: 从main.py中获取版本号，排除注释部分
for /f "tokens=2 delims= " %%a in ('findstr /C:"VERSION = " main.py ^| findstr /v /C:"#"') do (
    set "VERSION=%%a"
    set "VERSION=!VERSION:"=!"
)

:: 清空 dist 文件夹
if exist "dist" (
    rd /s /q "dist"
)
mkdir "dist"

:: 生成Windows应用包
python build.py

:: 删除旧的安装包，避免冲突
if exist "dist\TodoTracker-!VERSION!.exe" (
    del /f /q "dist\TodoTracker-!VERSION!.exe"
)

:: 重命名生成的文件
ren "dist\TodoTracker_release_!VERSION!.exe" "TodoTracker-!VERSION!.exe"

echo 打包完成: TodoTracker-!VERSION!.exe

:: 退出虚拟环境
call venv\Scripts\deactivate.bat

pause
