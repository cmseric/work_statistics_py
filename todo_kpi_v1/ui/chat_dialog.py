from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit,
    QLineEdit, QPushButton, QLabel, QWidget, QFrame,
    QScrollArea, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QTextCursor, QTextCharFormat, QTextBlockFormat, QColor, QFont, QTextDocument
from PyQt5.QtCore import QUrl
import requests
import json
import markdown
import re

def format_message(message):
    # 将markdown转换为HTML
    # Ensure message is not None before processing
    if message is None:
        message = ""
    html = markdown.markdown(message, extensions=['fenced_code', 'codehilite'])
    # 处理代码块
    html = re.sub(r'<pre><code( class="language-[^>"]*")?>', '<pre style="background-color: #f0f0f0; padding: 10px; border-radius: 5px; margin: 5px 0; overflow-x: auto;"><code style="font-family: Consolas, monospace; color: #333;">', html)
    html = re.sub(r'</code></pre>', '</code></pre>', html)
    # 处理段落
    html = re.sub(r'<p>', '<p style="margin: 5px 0;">', html)
    return html

class ChatDialog(QDialog):
    message_received = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI 助手")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
        """)
        
        self.init_ui()
        self.message_received.connect(self.append_message)
        
        # Typewriter effect state
        self.typing_target_edit = None
        self.typing_raw_content = ""
        self.current_display_content = ""
        self.typewriter_timer = QTimer(self)
        self.typewriter_timer.timeout.connect(self.type_next_char)
        
        # 初始化消息历史
        self.messages = []
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Chat history with scroll area
        self.scroll_area = QScrollArea() # Make scroll_area accessible
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #f0f2f5;
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f2f5;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #c1c1c1;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout()
        self.chat_layout.setAlignment(Qt.AlignTop) # Keep messages aligned to top
        self.chat_layout.setSpacing(15) # Increased spacing between messages
        self.chat_layout.setContentsMargins(10, 10, 10, 10)
        self.chat_container.setLayout(self.chat_layout)
        
        self.scroll_area.setWidget(self.chat_container)
        layout.addWidget(self.scroll_area)
        
        # Input area
        input_container = QFrame()
        input_container.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-top: 1px solid #e0e0e0;
            }
        """)
        input_layout = QHBoxLayout()
        input_layout.setContentsMargins(10, 10, 10, 10)
        
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("输入消息...")
        self.message_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #ddd;
                border-radius: 15px;
                background-color: #f5f5f5;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #2196F3;
                background-color: #ffffff;
            }
        """)
        self.message_input.returnPressed.connect(self.send_message)
        
        self.send_button = QPushButton("发送")
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 15px;
                font-size: 14px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
        """)
        self.send_button.clicked.connect(self.send_message)
        
        input_layout.addWidget(self.message_input)
        input_layout.addWidget(self.send_button)
        input_container.setLayout(input_layout)
        layout.addWidget(input_container)
        
        self.setLayout(layout)
        
    def send_message(self):
        # Stop any ongoing typing before sending a new message
        if self.typewriter_timer.isActive():
            self.typewriter_timer.stop()
            # Display the rest of the message instantly
            if self.typing_target_edit and self.typing_raw_content:
                 self.typing_target_edit.setHtml(format_message(self.typing_raw_content))
            self._reset_typing_state()

        message = self.message_input.text().strip()
        if not message:
            return
            
        # Add user message to chat and history
        user_message = {"role": "user", "content": message}
        self.messages.append(user_message)
        
        # 创建用户消息 (display instantly)
        self._add_message_to_chat(message, is_user=True, use_typewriter=False)
        
        self.message_input.clear()
        
        # Send to API
        try:
            # Indicate AI is thinking (optional)
            # self._add_message_to_chat("AI正在思考中...", is_user=False, use_typewriter=False)
            
            response = requests.post(
                "http://localhost:5010/api/chat",
                json={"messages": self.messages}
            )
            if response.status_code == 200:
                data = response.json()
                if data['success']:
                    ai_response_content = data['response']
                    # Add AI response to history
                    ai_message = {"role": "assistant", "content": ai_response_content}
                    self.messages.append(ai_message)
                    
                    # 创建AI消息 (use typewriter effect)
                    self._add_message_to_chat(ai_response_content, is_user=False, use_typewriter=True)
                else:
                    # Display error as AI message (instantly)
                    self._add_message_to_chat(f"错误: {data['error']}", is_user=False, use_typewriter=False)
            else:
                # Display error as AI message (instantly)
                self._add_message_to_chat(f"连接服务器失败: {response.status_code}", is_user=False, use_typewriter=False)
        except Exception as e:
            # Display error as AI message (instantly)
            self._add_message_to_chat(f"发生错误: {str(e)}", is_user=False, use_typewriter=False)
            
    def _add_message_to_chat(self, message_content, is_user, use_typewriter=False):
        # Ensure message_content is a string
        if not isinstance(message_content, str):
            message_content = str(message_content) 
            
        # Create name label
        name_label = QLabel("我" if is_user else "AI助手")
        name_color = "#008000" if is_user else "#0000FF" # Green for user, Blue for AI
        name_label.setStyleSheet(f"""
            QLabel {{
                font-weight: bold;
                color: {name_color};
                font-size: 12px;
                margin-left: {0 if not is_user else 5}px; 
                margin-right: {5 if is_user else 0}px; 
            }}
        """)
        
        # Create message content area (QTextEdit)
        message_edit = QTextEdit()
        message_edit.setReadOnly(True)
        message_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        message_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        message_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        message_edit.setMinimumHeight(30)
        message_edit.setMaximumHeight(16777215)
        message_edit.setLineWrapMode(QTextEdit.WidgetWidth)
        
        # 设置文档边距
        document = message_edit.document()
        document.setDocumentMargin(8)
        
        bg_color = "#e6ffed" if is_user else "#e3f2fd"
        message_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {bg_color};
                border: 1px solid #d0d0d0;
                border-radius: 8px;
                padding: 8px;
                font-size: 14px;
                line-height: 1.5;
            }}
            QTextEdit QScrollBar {{
                width: 0px;
                height: 0px;
            }}
        """)

        # Create vertical layout for name and message
        message_widget = QWidget()
        message_widget.setMaximumWidth(500)  # 限制消息最大宽度
        message_layout = QVBoxLayout()
        message_layout.setContentsMargins(0, 0, 0, 0)
        message_layout.addWidget(name_label)
        message_layout.addWidget(message_edit)
        message_widget.setLayout(message_layout)

        # Create horizontal layout for alignment
        container = QWidget()
        container_layout = QHBoxLayout()
        container_layout.setContentsMargins(0, 0, 0, 0)
        
        if is_user:
            # Align user message to the right
            name_label.setAlignment(Qt.AlignRight)
            container_layout.addStretch(1)
            container_layout.addWidget(message_widget)
        else:
            # Align AI message to the left
            name_label.setAlignment(Qt.AlignLeft)
            container_layout.addWidget(message_widget)
            container_layout.addStretch(1)
            
        container.setLayout(container_layout)
        self.chat_layout.addWidget(container)

        # Handle content display (instant or typewriter)
        if not is_user and use_typewriter:
            if self.typewriter_timer.isActive():
                self.typewriter_timer.stop()
                if self.typing_target_edit:
                    self.typing_target_edit.setHtml(format_message(self.typing_raw_content))
            
            self._reset_typing_state()
            message_edit.setHtml("")
            self.typing_target_edit = message_edit
            self.typing_raw_content = message_content
            self.current_display_content = ""
            self.typewriter_timer.start(50)
        else:
            message_edit.setHtml(format_message(message_content))
        
        # Scroll to bottom
        QTimer.singleShot(0, self._scroll_to_bottom)

    def _scroll_to_bottom(self):
        scrollbar = self.scroll_area.verticalScrollBar()
        if scrollbar: # Check if scrollbar exists
             scrollbar.setValue(scrollbar.maximum())
            
    def append_message(self, message, is_user=False): # Keep for compatibility if needed
        self._add_message_to_chat(message, is_user, use_typewriter=False)
        
    def type_next_char(self):
        if not self.typing_target_edit or self.typing_raw_content is None:
            self.typewriter_timer.stop()
            self._reset_typing_state()
            return

        if len(self.current_display_content) < len(self.typing_raw_content):
            next_char_index = len(self.current_display_content)
            self.current_display_content += self.typing_raw_content[next_char_index]
            
            # Update HTML and trigger layout recalculation for height
            self.typing_target_edit.setHtml(format_message(self.current_display_content))
            
            # Scroll to keep the typing visible
            self._scroll_to_bottom()
        else:
            # Finished typing
            self.typewriter_timer.stop()
            self._reset_typing_state()

    def _reset_typing_state(self):
        self.typing_target_edit = None
        self.typing_raw_content = ""
        self.current_display_content = ""
            
    def closeEvent(self, event):
        self.typewriter_timer.stop() # Stop timer on close
        super().closeEvent(event) 