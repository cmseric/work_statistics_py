import sys
import json
import csv
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton,
    QLineEdit, QLabel, QMessageBox, QFileDialog
)
from PyQt5.QtCore import Qt

DATA_FILE = "data.json"


class WorkTracker(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.load_data()

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
        self.table.setColumnWidth(2, 180)  # 增加操作列的列宽
        layout.addWidget(self.table)

        # 导出按钮
        self.export_button = QPushButton("导出数据")
        self.export_button.clicked.connect(self.export_data)
        layout.addWidget(self.export_button)

        self.setLayout(layout)

    def load_data(self):
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
        self.data[name]["last_action"] = "increase"  # 保存最后一次操作
        self.data[name]["count"] += 1
        self.save_data()
        self.refresh_table()

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
            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.table.setItem(row, 1, QTableWidgetItem(str(info["count"])))

            container = QWidget()
            btn_layout = QHBoxLayout(container)
            btn_layout.setContentsMargins(5, 2, 5, 2)  # 调整边距
            btn_layout.setSpacing(10)  # 调整按钮之间的间距

            plus_button = QPushButton("+1")
            plus_button.setFixedSize(50, 26)  # 调整按钮高度为 26
            plus_button.clicked.connect(lambda _, n=name: self.confirm_action('increase', n))

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