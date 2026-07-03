from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QScrollArea, QFrame, 
                             QListWidget, QListWidgetItem, QGraphicsDropShadowEffect)
from memory.history import get_recent_tasks

class TaskHistoryItem(QWidget):
    """Ancient-styled card widget for history items with soft parchment colors."""
    def __init__(self, task_type: str, query: str, response: str, timestamp: str, status: str, parent=None):
        super().__init__(parent)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(6, 6, 6, 6)
        
        # Container frame
        container = QFrame(self)
        container.setObjectName("HistoryItemContainer")
        
        # Style status borders (Emerald Green for success, Muted Crimson for failure)
        border_color = "#52b788" if status.upper() == "SUCCESS" else "#e63946"
        bg_color = "rgba(20, 24, 28, 0.6)"
        
        container.setStyleSheet(f"""
            QFrame#HistoryItemContainer {{
                background-color: {bg_color};
                border: 1px solid rgba(253, 240, 213, 0.08);
                border-left: 4px solid {border_color};
                border-radius: 8px;
                padding: 10px;
            }}
        """)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(6)
        
        # Header: Icon + Task Type + Timestamp
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        icons = {
            "open_app": "🔋 SUMMON APP",
            "find_file": "🔮 SEEK RUNES",
            "web_search": "☄️ ASTRAL QUERY",
            "draft_text": "📜 SCROLL SCRIBE",
            "set_reminder": "🔔 CHIME ALARM",
            "summarize_file": "📖 SCROLL TRANSLATE",
            "unknown": "💬 COMPANION TALK"
        }
        
        task_label = QLabel(icons.get(task_type, f"⚙️ {task_type.title()}"), container)
        task_label.setStyleSheet("color: #e09f3e; font-weight: 900; font-size: 11px; font-family: 'Segoe UI', Arial; letter-spacing: 0.5px;")
        
        time_label = QLabel(timestamp, container)
        time_label.setStyleSheet("color: #888899; font-size: 10px; font-family: 'Consolas', monospace;")
        time_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        header_layout.addWidget(task_label)
        header_layout.addWidget(time_label)
        
        # User query
        query_label = QLabel(f"Query: \"{query}\"", container)
        query_label.setStyleSheet("color: #fdf0d5; font-size: 12px; font-weight: bold;")
        query_label.setWordWrap(True)
        
        # Companion response
        resp_label = QLabel(response, container)
        resp_label.setStyleSheet("color: #a2d2ff; font-size: 11px; font-style: italic; font-family: 'Segoe UI';")
        resp_label.setWordWrap(True)
        
        layout.addLayout(header_layout)
        layout.addWidget(query_label)
        layout.addWidget(resp_label)
        
        main_layout.addWidget(container)

class AetherPanel(QWidget):
    submitted = pyqtSignal(str)
    settings_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Window properties
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint | 
            Qt.Tool | 
            Qt.SubWindow
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(370, 500)
        
        # Main Layout
        window_layout = QVBoxLayout(self)
        window_layout.setContentsMargins(10, 10, 10, 10)
        
        # Weathered Slate/Amber Style Panel Container
        self.container = QFrame(self)
        self.container.setObjectName("PanelContainer")
        self.container.setStyleSheet("""
            QFrame#PanelContainer {
                background-color: rgba(20, 24, 28, 0.96);
                border: 2px solid #e09f3e;
                border-radius: 16px;
            }
        """)
        
        # Warm amber glow drop shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(224, 159, 62, 160))
        shadow.setOffset(0, 0)
        self.container.setGraphicsEffect(shadow)
        
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(18, 18, 18, 18)
        container_layout.setSpacing(10)
        
        # --- Header Section ---
        header_layout = QHBoxLayout()
        
        title_label = QLabel("AETHER", self.container)
        title_label.setStyleSheet("""
            color: #fdf0d5; 
            font-size: 16px; 
            font-weight: 900; 
            font-family: 'Segoe UI', Arial;
            letter-spacing: 2.5px;
        """)
        
        # Status Layout
        self.status_dot = QFrame(self.container)
        self.status_dot.setFixedSize(10, 10)
        
        self.status_text = QLabel("Idle", self.container)
        self.status_text.setStyleSheet("color: #aaaaaa; font-size: 11px; font-weight: bold; font-family: 'Segoe UI';")
        
        self.set_status("idle")

        status_layout = QHBoxLayout()
        status_layout.setSpacing(6)
        status_layout.addWidget(self.status_dot)
        status_layout.addWidget(self.status_text)
        
        self.settings_btn = QPushButton("⚙️", self.container)
        self.settings_btn.setToolTip("Configure API Keys")
        self.settings_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #e09f3e;
                font-size: 14px;
                padding: 2px;
                cursor: pointer;
            }
            QPushButton:hover {
                color: #ffffff;
            }
        """)
        self.settings_btn.clicked.connect(self.settings_clicked.emit)

        header_layout.addWidget(title_label)
        header_layout.addWidget(self.settings_btn)
        header_layout.addStretch()
        header_layout.addLayout(status_layout)
        
        # Dragon Magic HUD Bar
        hud_bar = QLabel("DRAGON MAGIC: ACTIVE // GUARDIAN: STANDBY", self.container)
        hud_bar.setStyleSheet("""
            color: #e09f3e;
            font-family: 'Consolas', monospace;
            font-size: 10px;
            font-weight: bold;
            border: 1px solid rgba(224, 159, 62, 0.2);
            border-radius: 4px;
            padding: 4px 8px;
            background-color: rgba(224, 159, 62, 0.05);
        """)
        hud_bar.setAlignment(Qt.AlignCenter)
        
        # Divider line
        divider = QFrame(self.container)
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("background-color: rgba(224, 159, 62, 0.2); max-height: 1px; border: none;")
        
        # --- Recent Activity Log Scroll Area ---
        history_title = QLabel("ANCIENT SCROLL HISTORY", self.container)
        history_title.setStyleSheet("color: #e09f3e; font-size: 10px; font-weight: 900; letter-spacing: 1px;")
        
        self.history_list = QListWidget(self.container)
        self.history_list.setObjectName("HistoryList")
        self.history_list.setSelectionMode(QListWidget.NoSelection)
        self.history_list.setFocusPolicy(Qt.NoFocus)
        self.history_list.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        self.history_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.history_list.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        self.history_list.setStyleSheet("""
            QListWidget#HistoryList {
                background: transparent;
                border: none;
            }
        """)
        
        self.history_list.verticalScrollBar().setStyleSheet("""
            QScrollBar:vertical {
                background: rgba(0, 0, 0, 0.3);
                width: 8px;
                border-radius: 4px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #e09f3e, stop:1 #b5833f);
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #f4a261;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                background: none;
                border: none;
                height: 0px;
            }
            QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {
                background: none;
                border: none;
            }
        """)

        # --- Bottom Input Bar ---
        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)
        
        self.input_field = QLineEdit(self.container)
        self.input_field.setPlaceholderText("Command Aether (e.g. open chrome)...")
        self.input_field.setStyleSheet("""
            QLineEdit {
                background-color: rgba(0, 0, 0, 0.5);
                border: 1px solid rgba(224, 159, 62, 0.4);
                border-radius: 8px;
                color: #fdf0d5;
                padding: 8px 12px;
                font-size: 13px;
                font-family: 'Segoe UI';
            }
            QLineEdit:focus {
                border: 2px solid #f4a261;
                background-color: rgba(0, 0, 0, 0.7);
            }
        """)
        self.input_field.returnPressed.connect(self.submit_command)
        
        self.send_btn = QPushButton("COMMUNE", self.container)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #f4a261, stop:1 #e09f3e);
                border: 1px solid rgba(253, 240, 213, 0.2);
                border-radius: 8px;
                color: #14181c;
                font-weight: 900;
                font-size: 11px;
                padding: 8px 16px;
                font-family: 'Segoe UI';
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            QPushButton:hover {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffffff, stop:1 #f4a261);
            }
            QPushButton:pressed {
                background-color: #e09f3e;
            }
        """)
        self.send_btn.clicked.connect(self.submit_command)
        
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_btn)
        
        # Assemble layouts
        container_layout.addLayout(header_layout)
        container_layout.addWidget(hud_bar)
        container_layout.addWidget(divider)
        container_layout.addWidget(history_title)
        container_layout.addWidget(self.history_list)
        container_layout.addLayout(input_layout)
        
        window_layout.addWidget(self.container)
        self.reload_history()

    def set_status(self, state: str):
        """Sets status dot colors and texts matching dragon companion actions."""
        state = state.lower()
        if state == "listening":
            self.status_dot.setStyleSheet("background-color: #e76f51; border-radius: 5px; border: 1px solid #ffffff;")
            self.status_text.setText("COMMUNING...")
            self.status_text.setStyleSheet("color: #e76f51; font-size: 11px; font-weight: 900; font-family: 'Consolas', monospace;")
        elif state == "thinking":
            self.status_dot.setStyleSheet("background-color: #bb94ec; border-radius: 5px; border: 1px solid #ffffff;")
            self.status_text.setText("MEDITATING...")
            self.status_text.setStyleSheet("color: #bb94ec; font-size: 11px; font-weight: 900; font-family: 'Consolas', monospace;")
        elif state == "working":
            self.status_dot.setStyleSheet("background-color: #e09f3e; border-radius: 5px; border: 1px solid #ffffff;")
            self.status_text.setText("CASTING...")
            self.status_text.setStyleSheet("color: #e09f3e; font-size: 11px; font-weight: 900; font-family: 'Consolas', monospace;")
        else: # idle
            self.status_dot.setStyleSheet("background-color: #52b788; border-radius: 5px; border: 1px solid #ffffff;")
            self.status_text.setText("DRAGON STANDBY")
            self.status_text.setStyleSheet("color: #aaaaaa; font-size: 11px; font-weight: 700; font-family: 'Segoe UI';")

    def reload_history(self):
        """Fetches recent tasks and populates the scroll area history list."""
        self.history_list.clear()
        
        try:
            tasks = get_recent_tasks(limit=7)
            if not tasks:
                item = QListWidgetItem(self.history_list)
                label = QLabel("The dragon is quiet. Ask Aether to help you!", self.history_list)
                label.setStyleSheet("color: #777785; font-size: 12px; font-style: italic; padding: 20px;")
                label.setAlignment(Qt.AlignCenter)
                item.setSizeHint(QSize(300, 60))
                self.history_list.setItemWidget(item, label)
                return
                
            for task in tasks:
                item = QListWidgetItem(self.history_list)
                time_str = task["timestamp"]
                try:
                    time_parts = time_str.split(" ")
                    if len(time_parts) == 2:
                        date_parts = time_parts[0].split("-")
                        if len(date_parts) == 3:
                            time_str = f"{date_parts[1]}/{date_parts[2]} {time_parts[1][:5]}"
                except Exception:
                    pass
                    
                widget = TaskHistoryItem(
                    task_type=task["task_type"],
                    query=task["query"],
                    response=task["response"],
                    timestamp=time_str,
                    status=task["status"],
                    parent=self.history_list
                )
                item.setSizeHint(widget.sizeHint())
                self.history_list.addItem(item)
                self.history_list.setItemWidget(item, widget)
                
            self.history_list.scrollToTop()
        except Exception as e:
            print(f"Error loading task history: {str(e)}")

    def submit_command(self):
        text = self.input_field.text().strip()
        if text:
            self.input_field.clear()
            self.submitted.emit(text)

    def align_to_widget(self, widget_pos, widget_size):
        """Anchors the HUD panel next to the companion's current position."""
        from PyQt5.QtWidgets import QApplication
        
        screen = QApplication.primaryScreen().geometry()
        
        x = widget_pos.x() - self.width() - 8
        y = widget_pos.y() + widget_size.height() - self.height()
        
        if x < 0:
            x = widget_pos.x() + widget_size.width() + 8
            
        if y < 0:
            y = 10
            
        if y + self.height() > screen.height():
            y = screen.height() - self.height() - 50
            
        self.move(x, y)
        
    def showEvent(self, event):
        self.reload_history()
        super().showEvent(event)
