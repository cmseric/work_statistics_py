import sys
import PyInstaller.__main__
import datetime

timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
exe_name = f"TodoTracker_{timestamp}"

if sys.platform == 'win32':
    PyInstaller.__main__.run([
        'todo.py',
        '--onefile',
        '--windowed',
        '--name',
        exe_name,
        '--add-data',
        'favicon.ico:.',
        '--icon=favicon.ico'
    ])
elif sys.platform == 'darwin':
    PyInstaller.__main__.run([
        'todo.py',
        '--onefile',
        '--windowed',
        '--name',
        exe_name,
        '--add-data',
        'AppIcon.icns:.',
        '--icon=AppIcon.icns'
    ])
