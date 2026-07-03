from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QPoint, QSize
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtWidgets import (QDialog, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QFrame, QApplication, QGraphicsDropShadowEffect, QLineEdit)

class AetherConfirmDialog(QDialog):
    """Ancient scroll-styled custom confirmation dialog for destructive actions."""
    def __init__(self, title: str, filename: str, path: str, parent=None):
        super().__init__(parent)
        
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint | 
            Qt.Dialog
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(360, 210)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Slate container with amber border
        self.container = QFrame(self)
        self.container.setObjectName("ConfirmContainer")
        self.container.setStyleSheet("""
            QFrame#ConfirmContainer {
                background-color: rgba(20, 24, 28, 0.98);
                border: 2px solid #e09f3e;
                border-radius: 12px;
            }
        """)
        
        # Shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(224, 159, 62, 120))
        shadow.setOffset(0, 0)
        self.container.setGraphicsEffect(shadow)
        
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(20, 20, 20, 20)
        container_layout.setSpacing(12)
        
        # Title
        title_label = QLabel(title.upper(), self.container)
        title_label.setStyleSheet("""
            color: #e09f3e; 
            font-size: 13px; 
            font-weight: bold; 
            font-family: 'Segoe UI', Arial;
            letter-spacing: 1.5px;
        """)
        title_label.setAlignment(Qt.AlignCenter)
        
        # Question / File information
        desc_label = QLabel(f"Are you sure you want to banish this scroll into the void?\nIt will be lost forever.", self.container)
        desc_label.setStyleSheet("color: #fdf0d5; font-size: 11px; font-family: 'Segoe UI'; font-style: italic;")
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignCenter)
        
        file_label = QLabel(filename, self.container)
        file_label.setStyleSheet("color: #e63946; font-size: 13px; font-weight: bold; font-family: 'Consolas', monospace;")
        file_label.setWordWrap(True)
        file_label.setAlignment(Qt.AlignCenter)
        
        path_label = QLabel(path, self.container)
        path_label.setStyleSheet("color: #888899; font-size: 9px; font-family: 'Consolas', monospace;")
        path_label.setWordWrap(True)
        path_label.setAlignment(Qt.AlignCenter)
        
        # Buttons layout
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        
        self.btn_cancel = QPushButton("KEEP SCROLL", self.container)
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: rgba(253, 240, 213, 0.05);
                border: 1px solid #e09f3e;
                border-radius: 6px;
                color: #e09f3e;
                font-weight: bold;
                font-size: 11px;
                padding: 8px 16px;
                font-family: 'Segoe UI';
            }
            QPushButton:hover {
                background-color: rgba(224, 159, 62, 0.15);
            }
        """)
        self.btn_cancel.clicked.connect(self.reject)
        
        self.btn_confirm = QPushButton("BANISH IT", self.container)
        self.btn_confirm.setStyleSheet("""
            QPushButton {
                background-color: #e63946;
                border: 1px solid rgba(253, 240, 213, 0.2);
                border-radius: 6px;
                color: #ffffff;
                font-weight: bold;
                font-size: 11px;
                padding: 8px 16px;
                font-family: 'Segoe UI';
            }
            QPushButton:hover {
                background-color: #ff4d6d;
            }
        """)
        self.btn_confirm.clicked.connect(self.accept)
        
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_confirm)
        
        container_layout.addWidget(title_label)
        container_layout.addWidget(desc_label)
        container_layout.addWidget(file_label)
        container_layout.addWidget(path_label)
        container_layout.addStretch()
        container_layout.addLayout(btn_layout)
        
        layout.addWidget(self.container)
        
        # Center dialog relative to parent screen
        self.center_on_screen()
        
    def center_on_screen(self):
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)


class AetherRecordingBar(QWidget):
    """A floating, pill-shaped HUD for screen recording monitoring."""
    stop_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint | 
            Qt.Tool | 
            Qt.SubWindow
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(190, 50)
        
        self.drag_position = QPoint()
        self.dragging = False
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Pill container with glowing red/orange border
        self.container = QFrame(self)
        self.container.setObjectName("PillContainer")
        self.container.setStyleSheet("""
            QFrame#PillContainer {
                background-color: rgba(20, 24, 28, 0.95);
                border: 2px solid #e76f51;
                border-radius: 20px;
            }
        """)
        
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(12)
        shadow.setColor(QColor(231, 111, 81, 180))
        shadow.setOffset(0, 0)
        self.container.setGraphicsEffect(shadow)
        
        container_layout = QHBoxLayout(self.container)
        container_layout.setContentsMargins(12, 0, 12, 0)
        container_layout.setSpacing(8)
        
        # Flashing red dot
        self.dot = QFrame(self.container)
        self.dot.setFixedSize(10, 10)
        self.dot.setStyleSheet("background-color: #e63946; border-radius: 5px; border: 1px solid #ffffff;")
        
        # Timer Label
        self.timer_label = QLabel("REC 00:00", self.container)
        self.timer_label.setStyleSheet("color: #fdf0d5; font-size: 11px; font-weight: bold; font-family: 'Consolas', monospace;")
        
        # Stop Button
        self.stop_btn = QPushButton("STOP", self.container)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #e76f51, stop:1 #b54a30);
                border: none;
                border-radius: 12px;
                color: #ffffff;
                font-weight: 900;
                font-size: 9px;
                padding: 4px 10px;
                font-family: 'Segoe UI';
            }
            QPushButton:hover {
                background-color: #ff8870;
            }
        """)
        self.stop_btn.clicked.connect(self.stop_clicked.emit)
        
        container_layout.addWidget(self.dot)
        container_layout.addWidget(self.timer_label)
        container_layout.addStretch()
        container_layout.addWidget(self.stop_btn)
        
        layout.addWidget(self.container)
        
        # Timer logic
        self.seconds_elapsed = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_duration)
        
        self.flash_timer = QTimer(self)
        self.flash_timer.timeout.connect(self.toggle_dot_flash)
        self.dot_visible = True
        
        self.position_at_top()
        
    def position_at_top(self):
        screen = QApplication.primaryScreen().geometry()
        # Place at top right with some margin
        x = screen.width() - self.width() - 80
        y = 50
        self.move(x, y)
        
    def showEvent(self, event):
        self.seconds_elapsed = 0
        self.timer_label.setText("REC 00:00")
        self.timer.start(1000)
        self.flash_timer.start(500)
        super().showEvent(event)
        
    def hideEvent(self, event):
        self.timer.stop()
        self.flash_timer.stop()
        super().hideEvent(event)
        
    def update_duration(self):
        self.seconds_elapsed += 1
        mins = self.seconds_elapsed // 60
        secs = self.seconds_elapsed % 60
        self.timer_label.setText(f"REC {mins:02d}:{secs:02d}")
        
    def toggle_dot_flash(self):
        self.dot_visible = not self.dot_visible
        if self.dot_visible:
            self.dot.setStyleSheet("background-color: #e63946; border-radius: 5px; border: 1px solid #ffffff;")
        else:
            self.dot.setStyleSheet("background-color: transparent; border-radius: 5px; border: 1px solid transparent;")
            
    # Allow drag & drop movement of the recording bar
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            self.dragging = True
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.dragging:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False
            event.accept()


class AetherSpeechBubble(QWidget):
    """A floating, glassmorphic message bubble that appears above Aether's head."""
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint | 
            Qt.Tool | 
            Qt.SubWindow
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        
        self.container = QFrame(self)
        self.container.setObjectName("BubbleContainer")
        self.container.setStyleSheet("""
            QFrame#BubbleContainer {
                background-color: rgba(20, 24, 28, 0.95);
                border: 1.5px solid #e09f3e;
                border-radius: 12px;
            }
        """)
        
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(224, 159, 62, 100))
        shadow.setOffset(0, 0)
        self.container.setGraphicsEffect(shadow)
        
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(12, 8, 12, 8)
        
        self.label = QLabel(self.container)
        self.label.setStyleSheet("""
            color: #fdf0d5; 
            font-size: 11px; 
            font-family: 'Segoe UI', Arial;
            font-weight: 500;
        """)
        self.label.setWordWrap(True)
        self.label.setAlignment(Qt.AlignCenter)
        
        container_layout.addWidget(self.label)
        layout.addWidget(self.container)
        
        # Timer to auto-hide
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.fade_out_and_close)
        
        # Opacity for fade effect
        self.current_opacity = 0.0
        self.setWindowOpacity(self.current_opacity)
        
        self.fade_timer = QTimer(self)
        self.fade_timer.timeout.connect(self.fade_in)
        
    def show_text(self, text: str, widget_pos, widget_size, duration_ms=4000):
        self.label.setText(text)
        
        # Determine size based on text length dynamically
        text_len = len(text)
        if text_len < 20:
            self.setFixedSize(140, 52)
        elif text_len < 50:
            self.setFixedSize(180, 60)
        elif text_len < 100:
            self.setFixedSize(220, 72)
        else:
            self.setFixedSize(250, 88)
            
        self.align_to_widget(widget_pos, widget_size)
        self.show()
        
        # Start fade-in
        self.current_opacity = 0.0
        self.setWindowOpacity(self.current_opacity)
        self.fade_timer.start(30)
        
        # Schedule auto-hide
        self.hide_timer.start(duration_ms)
        
    def align_to_widget(self, widget_pos, widget_size):
        # Position bubble directly above Aether's head
        x = widget_pos.x() + (widget_size.width() - self.width()) // 2
        y = widget_pos.y() - self.height() + 8  # overlap slightly for aesthetics
        self.move(x, y)
        
    def fade_in(self):
        if self.current_opacity < 0.95:
            self.current_opacity += 0.15
            self.setWindowOpacity(min(0.95, self.current_opacity))
        else:
            self.fade_timer.stop()
            
    def fade_out_and_close(self):
        self.hide_timer.stop()
        self.fade_timer.stop()
        self.close()


class AetherSettingsDialog(QDialog):
    """Ancient scroll-styled custom settings dialog for entering API keys."""
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint | 
            Qt.Dialog
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(380, 290)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        self.container = QFrame(self)
        self.container.setObjectName("SettingsContainer")
        self.container.setStyleSheet("""
            QFrame#SettingsContainer {
                background-color: rgba(20, 24, 28, 0.98);
                border: 2px solid #e09f3e;
                border-radius: 12px;
            }
        """)
        
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(224, 159, 62, 120))
        shadow.setOffset(0, 0)
        self.container.setGraphicsEffect(shadow)
        
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(20, 15, 20, 15)
        container_layout.setSpacing(10)
        
        # Title
        title_label = QLabel("DRAGON MAGIC PORTAL", self.container)
        title_label.setStyleSheet("""
            color: #e09f3e; 
            font-size: 13px; 
            font-weight: bold; 
            font-family: 'Segoe UI', Arial;
            letter-spacing: 1.5px;
        """)
        title_label.setAlignment(Qt.AlignCenter)
        
        # Label descriptions and inputs
        gemini_label = QLabel("GEMINI API KEY:", self.container)
        gemini_label.setStyleSheet("color: #fdf0d5; font-size: 10px; font-weight: bold; font-family: 'Segoe UI';")
        
        self.gemini_input = QLineEdit(self.container)
        self.gemini_input.setEchoMode(QLineEdit.Password)
        self.gemini_input.setPlaceholderText("Paste Gemini API key here...")
        self.gemini_input.setStyleSheet(self.input_stylesheet())
        
        groq_label = QLabel("GROQ API KEY (OPTIONAL):", self.container)
        groq_label.setStyleSheet("color: #fdf0d5; font-size: 10px; font-weight: bold; font-family: 'Segoe UI';")
        
        self.groq_input = QLineEdit(self.container)
        self.groq_input.setEchoMode(QLineEdit.Password)
        self.groq_input.setPlaceholderText("Paste Groq API key here...")
        self.groq_input.setStyleSheet(self.input_stylesheet())
        
        # Help link
        help_label = QLabel('<a href="https://aistudio.google.com/" style="color: #a2d2ff; text-decoration: none;">Get a free Gemini API Key here 🔗</a>', self.container)
        help_label.setStyleSheet("font-size: 10px; font-family: 'Segoe UI';")
        help_label.setOpenExternalLinks(True)
        help_label.setAlignment(Qt.AlignCenter)
        
        # Buttons layout
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        
        self.btn_cancel = QPushButton("CANCEL", self.container)
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: rgba(253, 240, 213, 0.05);
                border: 1px solid #e09f3e;
                border-radius: 6px;
                color: #e09f3e;
                font-weight: bold;
                font-size: 10px;
                padding: 6px 16px;
                font-family: 'Segoe UI';
            }
            QPushButton:hover {
                background-color: rgba(224, 159, 62, 0.15);
            }
        """)
        self.btn_cancel.clicked.connect(self.reject)
        
        self.btn_save = QPushButton("SAVE RUNE KEYS", self.container)
        self.btn_save.setStyleSheet("""
            QPushButton {
                background-color: #e09f3e;
                border: 1px solid rgba(253, 240, 213, 0.2);
                border-radius: 6px;
                color: #14181c;
                font-weight: bold;
                font-size: 10px;
                padding: 6px 16px;
                font-family: 'Segoe UI';
            }
            QPushButton:hover {
                background-color: #f4a261;
            }
        """)
        self.btn_save.clicked.connect(self.save_keys)
        
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save)
        
        container_layout.addWidget(title_label)
        container_layout.addWidget(gemini_label)
        container_layout.addWidget(self.gemini_input)
        container_layout.addWidget(groq_label)
        container_layout.addWidget(self.groq_input)
        container_layout.addWidget(help_label)
        container_layout.addStretch()
        container_layout.addLayout(btn_layout)
        
        layout.addWidget(self.container)
        self.center_on_screen()
        self.load_current_keys()
        
    def input_stylesheet(self):
        return """
            QLineEdit {
                background-color: rgba(0, 0, 0, 0.5);
                border: 1px solid rgba(224, 159, 62, 0.4);
                border-radius: 6px;
                color: #fdf0d5;
                padding: 6px 10px;
                font-size: 11px;
                font-family: 'Consolas', monospace;
            }
            QLineEdit:focus {
                border: 1.5px solid #f4a261;
                background-color: rgba(0, 0, 0, 0.7);
            }
        """
        
    def center_on_screen(self):
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
        
    def load_current_keys(self):
        from utils.config import GEMINI_API_KEY, GROQ_API_KEY
        self.gemini_input.setText(GEMINI_API_KEY or "")
        self.groq_input.setText(GROQ_API_KEY or "")
        
    def save_keys(self):
        from pathlib import Path
        gemini_key = self.gemini_input.text().strip()
        groq_key = self.groq_input.text().strip()
        
        env_dir = Path.home() / ".aether"
        env_dir.mkdir(parents=True, exist_ok=True)
        env_file = env_dir / ".env"
        
        # Write keys to .env
        try:
            with open(env_file, "w") as f:
                f.write(f"GEMINI_API_KEY={gemini_key}\n")
                f.write(f"GROQ_API_KEY={groq_key}\n")
            
            # Dynamically update the config loaded keys in memory
            from utils import config
            config.GEMINI_API_KEY = gemini_key
            config.GROQ_API_KEY = groq_key
            
            self.accept()
        except Exception as e:
            print(f"Error saving keys: {e}")
            self.reject()
