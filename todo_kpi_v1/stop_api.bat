@echo off
echo 正在查找占用5010端口的进程...

:: 查找占用5010端口的进程ID
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5010') do (
    set "pid=%%a"
    echo 找到进程ID: !pid!
    
    :: 终止进程
    taskkill /F /PID !pid!
    echo 已终止进程
)

echo 端口5010已释放
pause 