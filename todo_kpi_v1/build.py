import sys
import PyInstaller.__main__
import datetime
import json
import os

# 获取当前脚本所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))
# 获取项目根目录（当前目录的上一级）
root_dir = os.path.dirname(current_dir)

print(f"当前目录: {current_dir}")
print(f"根目录: {root_dir}")

# 从main.py中获取版本号
VERSION = None
with open(os.path.join(current_dir, 'main.py'), 'r', encoding='utf-8') as f:
    for line in f:
        if line.startswith('VERSION ='):
            # 移除注释部分并提取版本号
            version_line = line.split('#')[0].strip()
            VERSION = version_line.split('=')[1].strip().strip('"\'')
            break

if not VERSION:
    raise ValueError("无法从main.py中获取版本号")

print(f"版本号: {VERSION}")

timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
exe_name = f"TodoTracker"

# 设置工作目录为todo_kpi_v1目录
os.chdir(current_dir)
print(f"工作目录已切换到: {os.getcwd()}")

# 构建资源文件路径（相对于todo_kpi_v1目录）
main_py = 'main.py'
favicon = 'favicon.ico'
version_file = 'version_info.txt'
requirements = 'requirements.txt'

print(f"主程序路径: {main_py}")
print(f"图标路径: {favicon}")
print(f"版本文件路径: {version_file}")

# 检查文件是否存在
for file_path in [main_py, favicon, version_file, requirements]:
    if not os.path.exists(file_path):
        print(f"警告: 文件不存在 - {file_path}")
    else:
        print(f"文件存在: {file_path}")

if sys.platform == 'win32':
    PyInstaller.__main__.run([
        main_py,
        '--onefile',
        '--windowed',
        '--name',
        exe_name,
        '--add-data',
        f"{favicon};.",
        '--icon=' + favicon,
        '--version-file=' + version_file,
        '--clean',
        '--noconfirm',
        '--hidden-import=PyQt5',
        '--hidden-import=PyQt5.QtCore',
        '--hidden-import=PyQt5.QtGui',
        '--hidden-import=PyQt5.QtWidgets',
        '--hidden-import=requests',
        '--hidden-import=json',
        '--hidden-import=datetime',
        '--hidden-import=logging',
        '--hidden-import=enum',
        '--hidden-import=shutil',
        '--hidden-import=subprocess',
        '--hidden-import=csv',
        '--hidden-import=os',
        '--hidden-import=sys',
        '--hidden-import=pytz',
        '--hidden-import=flask',
        '--hidden-import=flask_sqlalchemy',
        '--log-level=DEBUG'
    ])
elif sys.platform == 'darwin':
    bundle_id = 'com.cmseric.TodoTracker'
    app_icon = 'AppIcon.icns'

    PyInstaller.__main__.run([
        main_py,
        '--onefile',
        '--windowed',
        '--name',
        exe_name,
        '--add-data',
        f"{app_icon}:.",
        '--icon=' + app_icon,
        '--osx-bundle-identifier',
        bundle_id,
        '--version-file=' + version_file,
        '--clean',
        '--noconfirm',
        '--hidden-import=PyQt5',
        '--hidden-import=PyQt5.QtCore',
        '--hidden-import=PyQt5.QtGui',
        '--hidden-import=PyQt5.QtWidgets',
        '--hidden-import=requests',
        '--hidden-import=json',
        '--hidden-import=datetime',
        '--hidden-import=logging',
        '--hidden-import=enum',
        '--hidden-import=shutil',
        '--hidden-import=subprocess',
        '--hidden-import=csv',
        '--hidden-import=os',
        '--hidden-import=sys',
        '--hidden-import=pytz',
        '--hidden-import=flask',
        '--hidden-import=flask_sqlalchemy',
        '--log-level=DEBUG'
    ])

print("打包完成")
