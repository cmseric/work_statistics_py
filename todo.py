import os
import sys
import json
import logging
import csv
import shutil

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton,
    QLineEdit, QLabel, QMessageBox, QTabWidget,
    QComboBox, QProgressBar, QDateEdit, QInputDialog,
    QSizePolicy, QCheckBox, QFileDialog, QDialog,
    QDialogButtonBox
)
from PyQt5.QtCore import Qt, QDate, QDateTime
from PyQt5.QtGui import QIcon


def get_base_path():
    """获取跨平台数据存储路径"""
    if getattr(sys, 'frozen', False):
        app_name = "TodoTracker"
        if sys.platform == "win32":
            data_dir = os.path.join(os.getenv('APPDATA'), app_name)
        elif sys.platform == "darwin":
            data_dir = os.path.expanduser(f'~/Library/Application Support/{app_name}')
        else:  # Linux
            data_dir = os.path.expanduser(f'~/.config/{app_name}')
    else:
        data_dir = os.path.dirname(os.path.abspath(__file__))

    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir)


DATA_DIR = get_base_path()
DATA_FILE = os.path.join(DATA_DIR, "data_todo.json")

logging.basicConfig(
    filename=os.path.join(DATA_DIR, "debug.log"),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)


class ProgressType:
    ABSOLUTE = "absolute"
    CUMULATIVE = "cumulative"


class DataManager:
    def __init__(self):
        self.data = self._load_initial_data()
        self.window_size = self.data.get("window_size", [800, 500])

    def _load_initial_data(self):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"projects": {}, "todos": [], "window_size": [800, 500]}

    def save(self, window_size=None):
        if window_size:
            self.data["window_size"] = window_size
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)


data_mgr = DataManager()


class AutoStartManager:
    def __init__(self, app_name="TodoTracker"):
        self.app_name = app_name
        self.startup_folder = ''
        self.shortcut_path = ''
        self.init_state()

    def init_state(self):
        if sys.platform == "win32":
            self.startup_folder = os.path.join(
                os.getenv('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup'
            )
            self.shortcut_path = os.path.join(
                self.startup_folder,
                f'{self.app_name}.lnk'
            )
        elif sys.platform == "darwin":
            self.startup_folder = os.path.expanduser('~/Library/LaunchAgents')
            self.shortcut_path = os.path.join(
                self.startup_folder,
                f"{self.app_name}.plist"
            )
        else:  # Linux
            self.startup_folder = os.path.expanduser(f'~/.config/autostart')
            self.shortcut_path = os.path.expanduser(f'~/.config/autostart/{self.app_name}.desktop')

    def enable(self):
        if sys.platform == "win32":
            self._create_windows_shortcut()
        elif sys.platform == "darwin":
            self._create_macos_launchagent()
        else:
            self._create_linux_desktop_entry()

    def disable(self):
        if os.path.exists(self.shortcut_path):
            os.remove(self.shortcut_path)

    def _create_windows_shortcut(self):
        # import winshell
        from win32com.client import Dispatch

        shortcut = Dispatch('WScript.Shell').CreateShortCut(self.shortcut_path)
        shortcut.TargetPath = sys.executable
        shortcut.WorkingDirectory = os.path.dirname(sys.executable)
        shortcut.save()

    def _create_macos_launchagent(self):
        """创建macOS自启动服务"""
        try:
            # 确定应用路径
            if getattr(sys, 'frozen', False):
                # 打包应用模式
                app_path = os.path.dirname(sys.executable)
                if ".app/Contents/MacOS" in app_path:
                    app_bundle = app_path.split(".app/Contents/MacOS")[0] + ".app"
                    executable = f'"{app_bundle}/Contents/MacOS/{os.path.basename(sys.executable)}"'
                else:
                    executable = f'"{sys.executable}"'
            else:
                # 开发模式
                executable = f'"{sys.executable}" "{os.path.abspath(__file__)}"'

            # 创建plist内容
            plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
    <plist version="1.0">
    <dict>
        <key>Label</key>
        <string>com.cmseric.{self.app_name}</string>
        <key>ProgramArguments</key>
        <array>
            <string>/bin/sh</string>
            <string>-c</string>
            <string>{executable}</string>
        </array>
        <key>RunAtLoad</key>
        <true/>
        <key>KeepAlive</key>
        <false/>
    </dict>
    </plist>"""

            # 确保目录存在
            os.makedirs(os.path.dirname(self.shortcut_path), exist_ok=True)

            # 写入plist文件
            with open(self.shortcut_path, 'w') as f:
                f.write(plist_content)

            # 设置文件权限
            os.chmod(self.shortcut_path, 0o644)

        except Exception as e:
            logging.error(f"创建macOS自启动失败: {str(e)}")
            raise

    def _create_linux_desktop_entry(self):
        if not os.path.exists(self.startup_folder):
            os.makedirs(self.startup_folder)
        with open(self.shortcut_path, 'w') as f:
            f.write(f"""[Desktop Entry]
        Type=Application
        Exec={sys.executable} {os.path.abspath(__file__)}
        Hidden=false
        NoDisplay=false
        X-GNOME-Autostart-enabled=true
        Name=WorkTracker
        Comment=Start WorkTracker on login
        """)


autostart_mgr = AutoStartManager()


class WorkTracker(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.init_state()
        self.refresh_table()

    def init_state(self):
        # 窗口尺寸初始化
        self.resize(*data_mgr.window_size)

        # 自启动状态初始化
        self.autostart_checkbox.setChecked(
            os.path.exists(autostart_mgr.shortcut_path)
        )

    def initUI(self):
        self.setWindowTitle("TodoTracker")
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

        self.import_btn = QPushButton("导入数据")
        self.import_btn.clicked.connect(self.import_data)
        btn_layout.addWidget(self.import_btn)

        self.export_btn = QPushButton("导出全部数据")
        self.export_btn.clicked.connect(self.export_all_data)
        btn_layout.addWidget(self.export_btn)

        layout.addWidget(btn_container)

        self.setLayout(layout)

    def toggle_autostart(self, state):
        if state == Qt.Checked:
            autostart_mgr.enable()
        else:
            autostart_mgr.disable()

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
        table.setColumnWidth(4, 100)   # 截止时间列
        if len(headers) > 5:
            table.setColumnWidth(5, 100)  # 完成时间列
        table.setColumnWidth(len(headers) - 1, 220)  # 操作列

    def create_tab(self, table):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(table)
        widget.setLayout(layout)
        return widget

    def refresh_table(self):
        self.update_type_combo()
        self.refresh_summary_table()
        self.refresh_todo_tables()

    def update_type_combo(self):
        self.todo_type_input.clear()
        for name, info in data_mgr.data["projects"].items():
            self.todo_type_input.addItem(f"{name} ({info['unit']})")

    def add_project(self):
        name = self.name_input.text().strip()
        unit = self.unit_input.text().strip()
        progress_type = ProgressType.ABSOLUTE if self.progress_type_combo.currentIndex() == 0 else ProgressType.CUMULATIVE

        if name and unit and name not in data_mgr.data["projects"]:
            data_mgr.data["projects"][name] = {
                "unit": unit,
                "count": 0,
                "progress_type": progress_type
            }
            self.update_type_combo()
            data_mgr.save()
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

        project = data_mgr.data["projects"][type_name]

        data_mgr.data["todos"].append({
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
        data_mgr.save()
        self.refresh_todo_tables()

    def refresh_summary_table(self):
        self.table.setRowCount(len(data_mgr.data["projects"]))
        for row, (name, info) in enumerate(data_mgr.data["projects"].items()):
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

        for idx, todo in enumerate(data_mgr.data["todos"]):
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

                # Edit button
                edit_btn = QPushButton("编辑")
                edit_btn.clicked.connect(lambda _, i=idx: self.edit_todo(i))
                btn_layout.addWidget(edit_btn)

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
        todo = data_mgr.data["todos"][index]
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
                data_mgr.data["todos"][index]["progress"] = value
            else:
                data_mgr.data["todos"][index]["progress"] += value

            # 检查是否完成
            if data_mgr.data["todos"][index]["progress"] >= todo["target"]:
                self.complete_todo(index)

            data_mgr.save()
            self.refresh_todo_tables()

    def complete_todo(self, index):
        todo = data_mgr.data["todos"][index]
        todo["completed"] = True
        todo["complete_time"] = QDate.currentDate().toString("yyyy-MM-dd")
        data_mgr.data["projects"][todo["type"]]["count"] += 1
        data_mgr.save()

    def delete_project(self, row):
        name = list(data_mgr.data["projects"].keys())[row]
        del data_mgr.data["projects"][name]
        self.update_type_combo()
        data_mgr.save()
        self.refresh_summary_table()

    def delete_todo(self, index):
        del data_mgr.data["todos"][index]
        data_mgr.save()
        self.refresh_todo_tables()

    def restore_todo(self, index):
        todo = data_mgr.data["todos"][index]
        todo["completed"] = False
        if "complete_time" in todo:
            del todo["complete_time"]
        data_mgr.data["projects"][todo["type"]]["count"] -= 1
        data_mgr.save()
        self.refresh_todo_tables()

    def edit_todo(self, index):
        todo = data_mgr.data["todos"][index]
        dialog = QDialog(self)
        dialog.setWindowTitle("编辑TODO项")
        layout = QVBoxLayout()

        # 名称编辑
        name_edit = QLineEdit(todo["name"])
        layout.addWidget(QLabel("名称:"))
        layout.addWidget(name_edit)

        # 目标编辑
        target_edit = QLineEdit(str(todo["target"]))
        layout.addWidget(QLabel("目标:"))
        layout.addWidget(target_edit)

        # 截止时间选择
        deadline_edit = QDateEdit(QDate.fromString(todo["deadline"], "yyyy-MM-dd"))
        deadline_edit.setCalendarPopup(True)
        layout.addWidget(QLabel("截止时间:"))
        layout.addWidget(deadline_edit)

        # 进度编辑（根据类型）
        if todo["progress_type"] == ProgressType.ABSOLUTE:
            progress_edit = QLineEdit(str(todo["progress"]))
            layout.addWidget(QLabel("当前进度:"))
            layout.addWidget(progress_edit)
        else:
            progress_label = QLabel(str(todo["progress"]))
            layout.addWidget(QLabel("累计进度:"))
            layout.addWidget(progress_label)

        # 确认按钮
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(dialog.accept)
        btn_box.rejected.connect(dialog.reject)
        layout.addWidget(btn_box)

        dialog.setLayout(layout)

        if dialog.exec_() == QDialog.Accepted:
            try:
                # 数据校验
                new_target = float(target_edit.text())
                new_deadline = deadline_edit.date().toString("yyyy-MM-dd")

                # 更新数据
                todo.update({
                    "name": name_edit.text(),
                    "target": new_target,
                    "deadline": new_deadline
                })

                # 处理绝对进度更新
                if todo["progress_type"] == ProgressType.ABSOLUTE:
                    new_progress = float(progress_edit.text())
                    todo["progress"] = min(new_progress, new_target)

                data_mgr.save()
                self.refresh_todo_tables()

            except ValueError:
                QMessageBox.warning(self, "输入错误", "请输入有效的数字")

    def resizeEvent(self, event):
        # 窗口大小改变时实时保存
        data_mgr.data["window_size"] = [self.width(), self.height()]
        data_mgr.save()
        super().resizeEvent(event)

    def closeEvent(self, event):
        # 保存当前窗口尺寸
        data_mgr.data["window_size"] = [self.width(), self.height()]
        data_mgr.save()
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
        dir_path = QFileDialog.getExistingDirectory(self, "选择保存目录")
        if not dir_path: return

        try:
            timestamp = QDateTime.currentDateTime().toString("yyyyMMdd_hhmmss")
            export_dir = os.path.join(dir_path, f"export_{timestamp}")
            os.makedirs(export_dir, exist_ok=True)

            # 导出项目数据
            projects_path = os.path.join(export_dir, "projects.csv")
            with open(projects_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=["类型", "单位", "进度类型", "完成数量"])
                writer.writeheader()
                for name, info in data_mgr.data["projects"].items():
                    writer.writerow({
                        "类型": name,
                        "单位": info["unit"],
                        "进度类型": info["progress_type"],
                        "完成数量": info["count"]
                    })

            # 导出TODO数据
            todos_path = os.path.join(export_dir, "todos.csv")
            with open(todos_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "名称", "类型", "目标值", "当前进度", "进度类型",
                    "截止时间", "完成状态", "完成时间"
                ])
                writer.writeheader()
                for todo in data_mgr.data["todos"]:
                    writer.writerow({
                        "名称": todo["name"],
                        "类型": todo["type"],
                        "目标值": todo["target"],
                        "当前进度": todo["progress"],
                        "进度类型": todo["progress_type"],
                        "截止时间": todo["deadline"],
                        "完成状态": "已完成" if todo["completed"] else "进行中",
                        "完成时间": todo.get("complete_time", "")
                    })

            QMessageBox.information(self, "导出成功", f"数据已保存至：{export_dir}")

        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"错误信息：{str(e)}")

    def import_data(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择数据文件", "", "CSV文件 (*.csv)"
        )
        if not file_path: return

        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)

                if "单位" in reader.fieldnames:  # 项目数据
                    for row in reader:
                        name = row["类型"]
                        if name in data_mgr.data["projects"]:
                            # 更新现有项目
                            data_mgr.data["projects"][name].update({
                                "unit": row["单位"],
                                "progress_type": row["进度类型"],
                                "count": int(row["完成数量"])
                            })
                        else:
                            # 新增项目
                            data_mgr.data["projects"][name] = {
                                "unit": row["单位"],
                                "progress_type": row["进度类型"],
                                "count": int(row["完成数量"])
                            }

                elif "名称" in reader.fieldnames:  # TODO数据
                    for row in reader:
                        # 添加校验逻辑
                        required_fields = ["名称", "类型", "目标值", "进度类型", "截止时间"]
                        for field in required_fields:
                            if field not in row or not row[field]:
                                raise ValueError(f"缺少必要字段: {field}")

                        # 添加类型存在性校验
                        if row["类型"] not in data_mgr.data["projects"]:
                            raise ValueError(f"项目类型'{row['类型']}'尚未定义")

                        # 获取项目类型
                        type_name = row["类型"]

                        # 验证项目是否存在
                        if type_name not in data_mgr.data["projects"]:
                            QMessageBox.warning(self, "导入错误",
                                                f"项目类型'{type_name}'不存在，请先创建该类型")
                            continue

                        # 从已存在的项目中获取单位
                        unit = data_mgr.data["projects"][type_name]["unit"]

                        # 数据转换
                        todo = {
                            "name": row["名称"],
                            "type": row["类型"],
                            "unit": unit,
                            "target": float(row["目标值"]),
                            "progress": float(row["当前进度"]),
                            "progress_type": row["进度类型"],
                            "deadline": row["截止时间"],
                            "completed": row["完成状态"] == "已完成",
                            "complete_time": row["完成时间"] if row["完成状态"] == "已完成" else ""
                        }

                        # 避免重复添加
                        if not any(
                                t["name"] == todo["name"] and
                                t["type"] == todo["type"]
                                for t in data_mgr.data["todos"]
                        ):
                            data_mgr.data["todos"].append(todo)

            data_mgr.save()
            self.refresh_table()
            QMessageBox.information(self, "导入成功", "数据已成功加载")

        except Exception as e:
            QMessageBox.critical(self, "导入失败", f"数据解析错误：{str(e)}")

    def set_app_icon(self):
        icon_path = os.path.join(DATA_DIR, 'favicon.ico')

        # Windows特殊处理
        if sys.platform == 'win32':
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('TodoTracker.0.0.1')

        # MacOS特殊处理
        elif sys.platform == 'darwin':
            print("macos")
            # from Foundation import NSBundle
            # bundle = NSBundle.mainBundle()
            # info = bundle.localizedInfoDictionary() or bundle.infoDictionary()
            # info['CFBundleIconFile'] = 'AppIcon.'

        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            logging.warning(f"图标文件缺失: {icon_path}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WorkTracker()
    window.show()
    sys.exit(app.exec_())