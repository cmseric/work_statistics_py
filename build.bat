@echo off
setlocal enabledelayedexpansion
set "timestamp=%DATE:~0,4%%DATE:~5,2%%DATE:~8,2%_%TIME:~0,2%%TIME:~3,2%%TIME:~6,2%"
set "timestamp=!timestamp: =0!"  REM 去掉时间中的空格
pyinstaller -F -w -n "WorkTracker_%timestamp%" your_script.py
pause
