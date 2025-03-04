import PyInstaller.__main__
import datetime

timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
exe_name = f"WorkTracker_{timestamp}"

PyInstaller.__main__.run([
    'main.py',
    '--onefile',
    '--windowed',
    '--name', exe_name
])