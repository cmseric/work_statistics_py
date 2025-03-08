import sys
import PyInstaller.__main__
import datetime

timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
exe_name = f"TodoTracker"

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
    bundle_id = 'com.cmseric.TodoTracker'

    PyInstaller.__main__.run([
        'todo.py',
        '--onefile',
        '--windowed',
        '--name',
        exe_name,
        '--add-data',
        'AppIcon.icns:.',
        '--icon=AppIcon.icns',
        '--osx-bundle-identifier',
        bundle_id
    ])
