import os
import sys
import json
import csv
import logging
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton,
    QLineEdit, QLabel, QMessageBox, QFileDialog,
    QCheckBox
)
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation
from PyQt5.QtWidgets import QGraphicsOpacityEffect

# 获取当前脚本/程序所在的目录
if getattr(sys, 'frozen', False):  # 运行的是打包后的 .exe
    BASE_DIR = os.path.dirname(sys.executable)
else:  # 运行的是 .py 脚本
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_FILE = os.path.join(BASE_DIR, "data.json")

# 设置 log 文件路径
LOG_FILE = os.path.join(BASE_DIR, "debug.log")

# 配置 logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)

logging.debug("程序启动")


class WorkTracker(QWidget):
    def __init__(self):
        super().__init__()
        logging.debug("窗口初始化")
        self.initUI()
        self.load_data()
        # 存储每个项目的动画状态，防止叠加
        self.animations = {}

    def initUI(self):
        self.setWindowTitle("工作数据统计")
        self.setGeometry(100, 100, 600, 400)

        layout = QVBoxLayout()

        # 表单区域
        form_layout = QHBoxLayout()
        self.name_input = QLineEdit()
        self.add_button = QPushButton("添加类型")
        self.add_button.clicked.connect(self.add_project)
        form_layout.addWidget(QLabel("项目类型:"))
        form_layout.addWidget(self.name_input)
        form_layout.addWidget(self.add_button)
        layout.addLayout(form_layout)

        # 表格区域
        self.table = QTableWidget()
        self.table.setColumnCount(3)  # 删除撤回列，操作列改为 3 列
        self.table.setHorizontalHeaderLabels(["项目类型", "完成数量", "操作"])
        self.table.setColumnWidth(0, 200)
        self.table.setColumnWidth(2, 180)  # 增加操作列的列宽
        layout.addWidget(self.table)

        # 导出按钮
        self.export_button = QPushButton("导出数据")
        self.export_button.clicked.connect(self.export_data)
        layout.addWidget(self.export_button)

        # 开机自启动选项
        self.autostart_checkbox = QCheckBox("开机自动启动")
        self.autostart_checkbox.stateChanged.connect(self.toggle_autostart)
        layout.addWidget(self.autostart_checkbox)

        self.setLayout(layout)

        # 初始化自启动状态
        self.init_autostart()

    def init_autostart(self):
        if sys.platform == "win32":
            startup_folder = os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs',
                                          'Startup')
            shortcut_path = os.path.join(startup_folder, 'WorkTracker.lnk')
        elif sys.platform == "linux":
            startup_folder = os.path.expanduser('~/.config/autostart')
            shortcut_path = os.path.join(startup_folder, 'worktracker.desktop')
        else:
            return

        if os.path.exists(shortcut_path):
            self.autostart_checkbox.setChecked(True)

    def toggle_autostart(self, state):
        if sys.platform == "win32":
            startup_folder = os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs',
                                          'Startup')
            shortcut_path = os.path.join(startup_folder, 'WorkTracker.lnk')
        elif sys.platform == "linux":
            startup_folder = os.path.expanduser('~/.config/autostart')
            shortcut_path = os.path.join(startup_folder, 'worktracker.desktop')
        else:
            return

        if state == Qt.Checked:
            if sys.platform == "win32":
                import winshell
                from win32com.client import Dispatch
                shell = Dispatch('WScript.Shell')
                shortcut = shell.CreateShortCut(shortcut_path)
                shortcut.Targetpath = sys.executable
                shortcut.Arguments = os.path.abspath(__file__)
                shortcut.WorkingDirectory = os.path.dirname(os.path.abspath(__file__))
                shortcut.save()
            elif sys.platform == "linux":
                if not os.path.exists(startup_folder):
                    os.makedirs(startup_folder)
                with open(shortcut_path, 'w') as f:
                    f.write(f"""[Desktop Entry]
Type=Application
Exec={sys.executable} {os.path.abspath(__file__)}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name=WorkTracker
Comment=Start WorkTracker on login
""")
        else:
            if os.path.exists(shortcut_path):
                os.remove(shortcut_path)

    def load_data(self):
        logging.debug(f"Loading data from: {DATA_FILE}")
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                self.data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.data = {}
        self.refresh_table()

    def save_data(self):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)

    def add_project(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "警告", "项目类型不能为空！")
            return
        if name in self.data:
            QMessageBox.warning(self, "警告", "项目类型已存在！")
            return
        self.data[name] = {"count": 0, "last_action": None}  # 保存项目类型数据和操作记录
        self.name_input.clear()
        self.save_data()
        self.refresh_table()

    def confirm_action(self, action, name):
        """确认操作对话框"""
        reply = QMessageBox.question(
            self, "确认操作",
            f"确定要{'增加' if action == 'increase' else '减少' if action == 'decrease' else '删除'}项目类型 {name} 吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            if action == 'increase':
                self.increase_count(name)
            elif action == 'decrease':
                self.decrease_count(name)
            elif action == 'delete':
                self.delete_project(name)

    def increase_count(self, name):
        self.data[name]["last_action"] = "increase"
        self.data[name]["count"] += 1
        self.save_data()
        self.refresh_table()

        # 获取当前行号
        for row in range(self.table.rowCount()):
            if self.table.item(row, 0).text() == name:
                count_item = self.table.item(row, 1)
                self.animate_cell_color(name, count_item, QColor(144, 238, 144), QColor(255, 255, 255))
                break

    def animate_cell_color(self, name, item, start_color, end_color, duration=1000, steps=10):
        """使用 QTimer 让背景颜色平滑过渡，并防止动画重叠"""
        if name in self.animations:
            self.animations[name].stop()  # 停止之前的动画
            del self.animations[name]

        step_interval = duration // steps
        r_step = (end_color.red() - start_color.red()) / steps
        g_step = (end_color.green() - start_color.green()) / steps
        b_step = (end_color.blue() - start_color.blue()) / steps

        timer = QTimer(self)  # 使用 QTimer 实例
        timer.setInterval(step_interval)
        timer.setSingleShot(False)

        step = 0

        def update_color():
            nonlocal step
            if step > steps:
                timer.stop()
                del self.animations[name]  # 动画完成，清理状态
                return

            if not item:  # 防止访问失效的单元格
                timer.stop()
                del self.animations[name]
                return

            new_color = QColor(
                int(start_color.red() + r_step * step),
                int(start_color.green() + g_step * step),
                int(start_color.blue() + b_step * step)
            )
            item.setBackground(new_color)
            step += 1

        timer.timeout.connect(update_color)
        self.animations[name] = timer  # 存储动画
        timer.start()  # 启动动画

    def decrease_count(self, name):
        if self.data[name]["count"] > 0:
            self.data[name]["last_action"] = "decrease"
            self.data[name]["count"] -= 1
            self.save_data()
            self.refresh_table()
        else:
            QMessageBox.warning(self, "警告", "完成数量不能小于零！")

    def delete_project(self, name):
        self.data[name]["last_action"] = "delete"
        del self.data[name]
        self.save_data()
        self.refresh_table()

    def refresh_table(self):
        self.table.setRowCount(len(self.data))
        for row, (name, info) in enumerate(self.data.items()):
            name_item = QTableWidgetItem(name)
            name_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, name_item)

            count_item = QTableWidgetItem(str(info["count"]))
            count_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 1, count_item)

            container = QWidget()
            btn_layout = QHBoxLayout(container)
            btn_layout.setContentsMargins(5, 2, 5, 2)  # 调整边距
            btn_layout.setSpacing(10)  # 调整按钮之间的间距

            plus_button = QPushButton("+1")
            plus_button.setFixedSize(50, 26)  # 调整按钮高度为 26
            plus_button.clicked.connect(lambda _, n=name: self.increase_count(n))

            minus_button = QPushButton("-1")
            minus_button.setFixedSize(50, 26)  # 调整按钮高度为 26
            minus_button.clicked.connect(lambda _, n=name: self.confirm_action('decrease', n))

            del_button = QPushButton("删除")
            del_button.setFixedSize(60, 26)  # 调整按钮高度为 26
            del_button.clicked.connect(lambda _, n=name: self.confirm_action('delete', n))

            btn_layout.addWidget(del_button)
            btn_layout.addWidget(minus_button)
            btn_layout.addWidget(plus_button)
            btn_layout.setAlignment(Qt.AlignCenter)  # 让按钮居中对齐

            container.setLayout(btn_layout)
            self.table.setCellWidget(row, 2, container)

    def export_data(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "导出数据", "", "CSV 文件 (*.csv)")
        if file_path:
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["项目类型", "完成数量"])
                for name, info in self.data.items():
                    writer.writerow([name, info["count"]])
            QMessageBox.information(self, "成功", "数据导出成功！")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WorkTracker()
    window.show()
    sys.exit(app.exec_())