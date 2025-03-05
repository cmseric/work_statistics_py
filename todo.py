import os
import sys
import json
import logging
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton,
    QLineEdit, QLabel, QMessageBox, QTabWidget,
    QComboBox, QProgressBar, QDateEdit, QInputDialog,
    QSizePolicy, QCheckBox, QFileDialog
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QIcon

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_FILE = os.path.join(BASE_DIR, "data_todo.json")

logging.basicConfig(
    filename=os.path.join(BASE_DIR, "debug.log"),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)


class ProgressType:
    ABSOLUTE = "absolute"
    CUMULATIVE = "cumulative"


class WorkTracker(QWidget):
    def __init__(self):
        super().__init__()
        self.load_data()
        self.initUI()
        self.refresh_table()

    def initUI(self):
        self.setWindowTitle("TodoTracker")
        self.resize(*self.stored_size)  # 使用存储的尺寸
        self.set_app_icon()

        layout = QVBoxLayout()
        self.tabs = QTabWidget()

        self.init_summary_tab()
        self.init_todo_tab()

        layout.addWidget(self.tabs)

        # 在标签页下方添加统一导出按钮
        btn_container = QWidget()
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setContentsMargins(0, 10, 0, 0)  # 上边距10px
        btn_layout.addStretch(1)  # 左侧弹性空间

        self.autostart_checkbox = QCheckBox("开机自动启动")
        self.autostart_checkbox.stateChanged.connect(self.toggle_autostart)
        btn_layout.addWidget(self.autostart_checkbox)

        self.export_btn = QPushButton("导出全部数据")
        self.export_btn.clicked.connect(self.export_all_data)
        btn_layout.addWidget(self.export_btn)

        layout.addWidget(btn_container)

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

    def init_summary_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        form_layout = QHBoxLayout()

        self.name_input = QLineEdit()
        self.unit_input = QLineEdit("页")
        self.progress_type_combo = QComboBox()
        self.progress_type_combo.addItems(["准确进度", "累计进度"])
        self.add_button = QPushButton("添加类型")
        self.add_button.clicked.connect(self.add_project)

        form_layout.addWidget(QLabel("类型:"))
        form_layout.addWidget(self.name_input)
        form_layout.addWidget(QLabel("单位:"))
        form_layout.addWidget(self.unit_input)
        form_layout.addWidget(QLabel("进度类型:"))
        form_layout.addWidget(self.progress_type_combo)
        form_layout.addWidget(self.add_button)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["项目类型", "完成数量", "操作"])

        # 在表格初始化后添加
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)
        self.table.setColumnWidth(0, 120)  # 项目类型列
        self.table.setColumnWidth(1, 80)  # 完成数量列
        self.table.setColumnWidth(2, 100)  # 操作列

        layout.addLayout(form_layout)
        layout.addWidget(self.table)
        tab.setLayout(layout)
        self.tabs.addTab(tab, "完成统计")

    def init_todo_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        form_layout = QHBoxLayout()

        self.todo_name_input = QLineEdit()
        self.todo_type_input = QComboBox()
        self.todo_target_input = QLineEdit()
        self.todo_deadline_input = QDateEdit()
        self.todo_deadline_input.setDate(QDate.currentDate())
        self.todo_deadline_input.setDisplayFormat("yyyy-MM-dd")
        self.todo_deadline_input.setCalendarPopup(True)
        self.todo_add_button = QPushButton("添加 TODO")
        self.todo_add_button.clicked.connect(self.add_todo)

        form_layout.addWidget(QLabel("名称:"))
        form_layout.addWidget(self.todo_name_input)
        form_layout.addWidget(QLabel("类型:"))
        form_layout.addWidget(self.todo_type_input)
        form_layout.addWidget(QLabel("目标:"))
        form_layout.addWidget(self.todo_target_input)
        form_layout.addWidget(QLabel("截止时间:"))
        form_layout.addWidget(self.todo_deadline_input)
        form_layout.addWidget(self.todo_add_button)

        self.todo_tabs = QTabWidget()
        self.todo_table = QTableWidget()
        self.completed_table = QTableWidget()

        self.init_todo_table(self.todo_table, ["名称", "类型", "进度", "目标", "截止时间", "操作"])
        self.init_todo_table(self.completed_table, ["名称", "类型", "进度", "目标", "截止时间", "完成时间", "操作"])

        self.todo_tabs.addTab(self.create_tab(self.todo_table), "进行中")
        self.todo_tabs.addTab(self.create_tab(self.completed_table), "已完成")

        layout.addLayout(form_layout)
        layout.addWidget(self.todo_tabs)
        tab.setLayout(layout)
        self.tabs.addTab(tab, "TODO 进度")

    def init_todo_table(self, table, headers):
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)

        # 在初始化后添加列宽设置
        table.setColumnWidth(0, 140)  # 名称列
        table.setColumnWidth(1, 100)  # 类型列
        table.setColumnWidth(2, 190)  # 进度条列
        table.setColumnWidth(3, 100)  # 目标列
        table.setColumnWidth(4, 80)   # 截止时间列
        if len(headers) > 5:
            table.setColumnWidth(5, 80)  # 完成时间列
        table.setColumnWidth(len(headers) - 1, 120)  # 操作列

    def create_tab(self, table):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(table)
        widget.setLayout(layout)
        return widget

    def load_data(self):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                self.data = json.load(f)
                # 读取保存的窗口尺寸
                self.stored_size = self.data.get("window_size", [800, 500])
        except (FileNotFoundError, json.JSONDecodeError):
            self.data = {"projects": {}, "todos": [], "window_size": [800, 500]}  # 默认尺寸
            self.stored_size = (800, 500)

    def refresh_table(self):
        self.update_type_combo()
        self.refresh_summary_table()
        self.refresh_todo_tables()

    def update_type_combo(self):
        self.todo_type_input.clear()
        for name, info in self.data["projects"].items():
            self.todo_type_input.addItem(f"{name} ({info['unit']})")

    def save_data(self):
        # 确保每次保存都包含最新尺寸
        if not hasattr(self, 'data'):
            self.data = {}
        self.data["window_size"] = [self.width(), self.height()]

        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)

    def add_project(self):
        name = self.name_input.text().strip()
        unit = self.unit_input.text().strip()
        progress_type = ProgressType.ABSOLUTE if self.progress_type_combo.currentIndex() == 0 else ProgressType.CUMULATIVE

        if name and unit and name not in self.data["projects"]:
            self.data["projects"][name] = {
                "unit": unit,
                "count": 0,
                "progress_type": progress_type
            }
            self.update_type_combo()
            self.save_data()
            self.refresh_summary_table()

    def add_todo(self):
        name = self.todo_name_input.text().strip()
        type_str = self.todo_type_input.currentText()
        target = self.todo_target_input.text().strip()
        deadline = self.todo_deadline_input.date().toString("yyyy-MM-dd")

        if not (name and type_str and target):
            return

        try:
            target = float(target)
        except ValueError:
            QMessageBox.warning(self, "错误", "目标值必须是数字")
            return

        # 解析类型信息
        type_name, unit = type_str.split(" (")
        type_name = type_name.strip()
        unit = unit[:-1].strip()

        project = self.data["projects"][type_name]

        self.data["todos"].append({
            "name": name,
            "type": type_name,
            "unit": unit,
            "target": target,
            "progress": 0.0 if project["progress_type"] == ProgressType.CUMULATIVE else None,
            "progress_type": project["progress_type"],
            "deadline": deadline,
            "completed": False
        })

        self.todo_name_input.clear()
        self.todo_target_input.clear()
        self.save_data()
        self.refresh_todo_tables()

    def refresh_summary_table(self):
        self.table.setRowCount(len(self.data["projects"]))
        for row, (name, info) in enumerate(self.data["projects"].items()):
            unit_item = QTableWidgetItem(f"{name} ({info['unit']})")
            count_item = QTableWidgetItem(str(info["count"]))

            unit_item.setTextAlignment(Qt.AlignCenter)
            count_item.setTextAlignment(Qt.AlignCenter)

            self.table.setItem(row, 0, unit_item)
            self.table.setItem(row, 1, count_item)

            btn = QPushButton("删除")
            btn.clicked.connect(lambda _, r=row: self.delete_project(r))
            self.table.setCellWidget(row, 2, btn)

    def refresh_todo_tables(self):
        for table in [self.todo_table, self.completed_table]:
            table.setRowCount(0)

        for idx, todo in enumerate(self.data["todos"]):
            table = self.completed_table if todo["completed"] else self.todo_table
            row = table.rowCount()
            table.insertRow(row)

            # 基本信息
            table.setItem(row, 0, QTableWidgetItem(todo["name"]))
            table.setItem(row, 1, QTableWidgetItem(f"{todo['type']} ({todo['unit']})"))
            table.setItem(row, 3, QTableWidgetItem(f"{todo['progress']}/{todo['target']}{todo['unit']}"))
            table.setItem(row, 4, QTableWidgetItem(todo["deadline"]))

            # 进度显示
            progress = QProgressBar()
            # 添加固定尺寸设置
            progress.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            progress.setFixedHeight(20)  # 高度调整为20像素
            progress.setFixedWidth(180)

            if todo["progress_type"] == ProgressType.CUMULATIVE:
                progress_val = (todo["progress"] / todo["target"]) * 100
                progress.setValue(int(progress_val))
                # progress.setFormat(f"{todo['progress']}/{todo['target']}{todo['unit']}")
            else:
                if todo["progress"] is not None:
                    progress_val = (todo["progress"] / todo["target"]) * 100
                    progress.setValue(int(progress_val))
                    # progress.setFormat(f"{todo['progress']}{todo['unit']}")
                else:
                    progress.setValue(0)
                    progress.setFormat("未开始")

            cell_widget = QWidget()
            layout = QHBoxLayout(cell_widget)
            layout.setAlignment(Qt.AlignCenter)  # 水平垂直居中
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(progress)
            cell_widget.setLayout(layout)

            table.setCellWidget(row, 2, cell_widget)

            # 操作按钮
            btn_box = QWidget()
            btn_layout = QHBoxLayout()
            btn_layout.setContentsMargins(0, 0, 0, 0)

            if not todo["completed"]:
                update_btn = QPushButton("更新进度")
                update_btn.clicked.connect(lambda _, i=idx: self.update_progress(i))
                btn_layout.addWidget(update_btn)

            delete_btn = QPushButton("删除")
            delete_btn.clicked.connect(lambda _, i=idx: self.delete_todo(i))
            btn_layout.addWidget(delete_btn)

            if todo["completed"]:
                restore_btn = QPushButton("恢复")
                restore_btn.clicked.connect(lambda _, i=idx: self.restore_todo(i))
                btn_layout.addWidget(restore_btn)

            btn_box.setLayout(btn_layout)
            table.setCellWidget(row, 6 if todo["completed"] else 5, btn_box)

            # 完成时间
            if todo["completed"]:
                table.setItem(row, 5, QTableWidgetItem(todo.get("complete_time", "")))

    def update_progress(self, index):
        todo = self.data["todos"][index]
        dialog = QInputDialog(self)
        dialog.setWindowTitle("更新进度")

        if todo["progress_type"] == ProgressType.ABSOLUTE:
            dialog.setLabelText(f"当前进度（{todo['unit']}）:")
            dialog.setDoubleRange(0, todo["target"])
            dialog.setDoubleDecimals(0)
            dialog.setDoubleValue(todo["progress"] or 0)
        else:
            dialog.setLabelText(f"本次完成量（{todo['unit']}）:")
            dialog.setDoubleRange(0, todo["target"] - todo["progress"])
            dialog.setDoubleDecimals(1)
            dialog.setDoubleValue(0)

        if dialog.exec_() == QInputDialog.Accepted:
            value = dialog.doubleValue()

            if todo["progress_type"] == ProgressType.ABSOLUTE:
                self.data["todos"][index]["progress"] = value
            else:
                self.data["todos"][index]["progress"] += value

            # 检查是否完成
            if self.data["todos"][index]["progress"] >= todo["target"]:
                self.complete_todo(index)

            self.save_data()
            self.refresh_todo_tables()

    def complete_todo(self, index):
        todo = self.data["todos"][index]
        todo["completed"] = True
        todo["complete_time"] = QDate.currentDate().toString("yyyy-MM-dd")
        self.data["projects"][todo["type"]]["count"] += 1
        self.save_data()

    def delete_project(self, row):
        name = list(self.data["projects"].keys())[row]
        del self.data["projects"][name]
        self.update_type_combo()
        self.save_data()
        self.refresh_summary_table()

    def delete_todo(self, index):
        del self.data["todos"][index]
        self.save_data()
        self.refresh_todo_tables()

    def restore_todo(self, index):
        todo = self.data["todos"][index]
        todo["completed"] = False
        if "complete_time" in todo:
            del todo["complete_time"]
        self.data["projects"][todo["type"]]["count"] -= 1
        self.save_data()
        self.refresh_todo_tables()

    def resizeEvent(self, event):
        # 窗口大小改变时实时保存
        self.data["window_size"] = [self.width(), self.height()]
        self.save_data()
        super().resizeEvent(event)

    def closeEvent(self, event):
        # 保存当前窗口尺寸
        self.data["window_size"] = [self.width(), self.height()]
        self.save_data()
        super().closeEvent(event)

    def format_progress(self, todo):
        progress = todo["progress"]
        target = todo["target"]

        if progress is None:
            return "未开始"

        try:
            percentage = (progress / target) * 100
            # 保留1位小数，如：50(25.0%)
            return f"{progress}{todo['unit']}({percentage:.1f}%)"
        except ZeroDivisionError:
            return "无效目标"

    def export_all_data(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, "保存文件", "", "Excel文件 (*.xlsx)"
        )
        if not filename:
            return

        try:
            import pandas as pd

            # 准备数据
            projects_df = pd.DataFrame([
                {
                    "项目类型": name,
                    "单位": info["unit"],
                    "完成数量": info["count"],
                    "进度类型": info["progress_type"]
                }
                for name, info in self.data["projects"].items()
            ])

            todos_df = pd.DataFrame([
                {
                    "名称": todo["name"],
                    "类型": todo["type"],
                    "单位": todo["unit"],
                    "目标": todo["target"],
                    "当前进度": self.format_progress(todo),
                    "进度类型": todo["progress_type"],
                    "截止时间": todo["deadline"],
                    "完成状态": "是" if todo["completed"] else "否",
                    "完成时间": todo.get("complete_time", "")
                }
                for todo in self.data["todos"]
            ])

            # 写入Excel
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                projects_df.to_excel(writer, sheet_name='完成统计', index=False)
                todos_df.to_excel(writer, sheet_name='TODO列表', index=False)

                # 调整列宽
                for sheet in writer.sheets:
                    worksheet = writer.sheets[sheet]
                    worksheet.column_dimensions['A'].width = 20
                    worksheet.column_dimensions['B'].width = 15
                    worksheet.column_dimensions['C'].width = 10
                    worksheet.column_dimensions['D'].width = 15
                    worksheet.column_dimensions['E'].width = 20
                    worksheet.column_dimensions['F'].width = 15
                    worksheet.column_dimensions['G'].width = 15
                    worksheet.column_dimensions['H'].width = 10
                    worksheet.column_dimensions['I'].width = 15

            QMessageBox.information(self, "导出成功", f"文件已保存至：\n{filename}")

        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"错误信息：\n{str(e)}")

    def set_app_icon(self):
        icon_path = os.path.join(BASE_DIR, 'app.ico')

        # Windows特殊处理
        if sys.platform == 'win32':
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('TodoTracker.0.0.1')

        # MacOS特殊处理
        elif sys.platform == 'darwin':
            from Foundation import NSBundle
            bundle = NSBundle.mainBundle()
            info = bundle.localizedInfoDictionary() or bundle.infoDictionary()
            info['CFBundleIconFile'] = 'favicon.icns'

        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            logging.warning(f"图标文件缺失: {icon_path}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WorkTracker()
    window.show()
    sys.exit(app.exec_())