import os
import math
import random
import threading
import winsound
from PyQt5.QtCore import Qt, QPoint, pyqtSignal, QTimer, QSize
from PyQt5.QtGui import QPixmap, QIcon, QMouseEvent, QImage, QColor, QMovie
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QMenu, QSystemTrayIcon, QAction
from utils.config import AETHER_IDLE_PATH, AETHER_READY_PATH, AETHER_CHARGING_PATH, BASE_DIR

class SoundEffectThread(threading.Thread):
    """Plays Windows standard system WAV sounds asynchronously to prevent UI blocks."""
    def __init__(self, effect_type: str):
        super().__init__()
        self.effect_type = effect_type
        self.daemon = True

    def run(self):
        try:
            system_root = os.environ.get("SystemRoot", "C:\\Windows")
            
            if self.effect_type == "processing":
                # A quick, subtle notification click sound
                sound_path = os.path.join(system_root, "Media", "Windows Navigation Start.wav")
                if os.path.exists(sound_path):
                    winsound.PlaySound(sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
                else:
                    winsound.PlaySound("SystemDefault", winsound.SND_ALIAS | winsound.SND_ASYNC)
                    
            elif self.effect_type == "ready":
                # Magical upward chime (Windows Feed Discovered or Speech On)
                sound_path = os.path.join(system_root, "Media", "Windows Feed Discovered.wav")
                if not os.path.exists(sound_path):
                    sound_path = os.path.join(system_root, "Media", "Speech On.wav")
                
                if os.path.exists(sound_path):
                    winsound.PlaySound(sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
                else:
                    winsound.PlaySound("SystemQuestion", winsound.SND_ALIAS | winsound.SND_ASYNC)
                    
            elif self.effect_type == "relax":
                # Magical soft power-down (Speech Sleep)
                sound_path = os.path.join(system_root, "Media", "Speech Sleep.wav")
                if os.path.exists(sound_path):
                    winsound.PlaySound(sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
                else:
                    winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS | winsound.SND_ASYNC)
        except Exception:
            pass

class AetherWidget(QWidget):
    clicked = pyqtSignal()
    moved = pyqtSignal()
    double_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Transparent borderless overlay setup
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint | 
            Qt.Tool | 
            Qt.SubWindow
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        
        self.drag_position = QPoint()
        
        # Setup UI
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.label)
        
        self.setFixedSize(140, 140)
        
        # Keep track of positioning coordinates
        self.base_x = 0
        self.base_y = 0
        
        # State Management
        self.current_state = "idle"  # idle, processing, ready, sleep
        self.dragging = False
        self.shaking = False
        
        # Animation parameters
        self.bob_angle = 0.0
        
        # Animation Timers
        self.bob_timer = QTimer(self)
        self.bob_timer.timeout.connect(self.bob_aether)
        self.bob_timer.start(40)  # ~25 fps bobbing
        
        self.shake_timer = QTimer(self)
        self.shake_timer.timeout.connect(self.shake_aether)
        
        # Load Sprite
        self.load_sprite()
        
        # System Tray Icon Setup
        self.setup_tray()
        
        # Set size and position to bottom right of screen
        self.resize_and_position()
        
        self.setWindowOpacity(0.95)
        self.setCursor(Qt.PointingHandCursor)
        self.hovering = False

    def load_sprite(self):
        """Loads appropriate sprite path depending on the current state."""
        sprite_path = AETHER_IDLE_PATH
        if self.current_state == "ready" and os.path.exists(AETHER_READY_PATH):
            sprite_path = AETHER_READY_PATH
        elif self.current_state == "processing" and os.path.exists(AETHER_CHARGING_PATH):
            sprite_path = AETHER_CHARGING_PATH
            
        # Try loading animated GIF if it exists
        gif_path = sprite_path.with_suffix(".gif")
        if os.path.exists(gif_path):
            if hasattr(self, "movie") and self.movie:
                self.movie.stop()
                self.movie = None
                
            self.movie = QMovie(str(gif_path))
            self.movie.setScaledSize(QSize(130, 130))
            self.label.setMovie(self.movie)
            self.movie.start()
            self.label.setStyleSheet("")
            self.label.setText("")
        elif os.path.exists(sprite_path):
            if hasattr(self, "movie") and self.movie:
                self.movie.stop()
                self.movie = None
                
            pixmap = QPixmap(str(sprite_path))
            pixmap = self.make_image_transparent(pixmap)
            scaled_pixmap = pixmap.scaled(130, 130, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.label.setPixmap(scaled_pixmap)
            self.label.setStyleSheet("")
            self.label.setText("")
        else:
            # Fallback if image is missing: render a nice text orb
            color = "#e09f3e" if self.current_state == "ready" else "#ff9f1c" if self.current_state == "processing" else "#52b788"
            self.label.setStyleSheet(f"""
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {color}, stop:1 #3a506b);
                border: 2px solid #ffffff;
                border-radius: 50px;
                color: #ffffff;
                font-weight: bold;
                font-family: 'Segoe UI';
                font-size: 13px;
            """)
            self.label.setText("Ready" if self.current_state == "ready" else "Processing" if self.current_state == "processing" else "Hey Aether!")
            self.label.setAlignment(Qt.AlignCenter)
            self.label.setFixedSize(100, 100)

    def make_image_transparent(self, pixmap: QPixmap, threshold: int = 40) -> QPixmap:
        """
        Keys out the dark background from a QPixmap to make it transparent,
        using a flood-fill (BFS) algorithm starting from the outer boundary
        pixels to ensure inner black features (like dark eyes/scales) are not eroded.
        """
        image = pixmap.toImage().convertToFormat(QImage.Format_ARGB32)
        width, height = image.width(), image.height()
        
        # Sample background color from top-left corner
        bg_color = image.pixelColor(0, 0)
        bg_r, bg_g, bg_b = bg_color.red(), bg_color.green(), bg_color.blue()
        
        is_bg_dark = (bg_r < 45 and bg_g < 45 and bg_b < 45)
        
        # 2D list for fast visited-pixel tracking
        visited = [[False] * height for _ in range(width)]
        queue = []
        
        # Add all border pixels to start the BFS
        # Top and bottom edges
        for x in range(width):
            queue.append((x, 0))
            visited[x][0] = True
            queue.append((x, height - 1))
            visited[x][height - 1] = True
        # Left and right edges
        for y in range(1, height - 1):
            queue.append((0, y))
            visited[0][y] = True
            queue.append((width - 1, y))
            visited[width - 1][y] = True
            
        # BFS loop to flood fill background transparency
        while queue:
            x, y = queue.pop(0)
            
            c = image.pixelColor(x, y)
            r, g, b = c.red(), c.green(), c.blue()
            
            dist = math.sqrt((r - bg_r)**2 + (g - bg_g)**2 + (b - bg_b)**2)
            dist_black = math.sqrt(r**2 + g**2 + b**2)
            
            if dist < threshold or (is_bg_dark and dist_black < threshold):
                # Turn background pixel transparent
                image.setPixelColor(x, y, QColor(0, 0, 0, 0))
                
                # Check 4-directional neighbors
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < width and 0 <= ny < height:
                        if not visited[nx][ny]:
                            visited[nx][ny] = True
                            queue.append((nx, ny))
                            
        return QPixmap.fromImage(image)

    def resize_and_position(self):
        """Places the widget in the bottom-right corner of the primary screen, just above the taskbar."""
        from PyQt5.QtWidgets import QApplication
        
        screen = QApplication.primaryScreen().geometry()
        
        # Position slightly padded
        x = screen.width() - self.width() - 50
        y = screen.height() - self.height() - 80
        
        self.base_x = x
        self.base_y = y
        self.move(x, y)

    def setup_tray(self):
        """Adds Aether to the system tray."""
        self.tray_icon = QSystemTrayIcon(self)
        
        if os.path.exists(AETHER_IDLE_PATH):
            self.tray_icon.setIcon(QIcon(str(AETHER_IDLE_PATH)))
        else:
            self.tray_icon.setIcon(QIcon())
            
        tray_menu = QMenu()
        
        wake_action = QAction("Wake up Aether", self)
        wake_action.triggered.connect(self.clicked.emit)
        
        exit_action = QAction("Exit App", self)
        exit_action.triggered.connect(self.close_app)
        
        tray_menu.addAction(wake_action)
        tray_menu.addSeparator()
        tray_menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        self.tray_icon.activated.connect(self.on_tray_activated)

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.clicked.emit()

    def close_app(self):
        self.tray_icon.hide()
        from PyQt5.QtWidgets import QApplication
        QApplication.quit()

    # --- Animation Physics ---

    def bob_aether(self):
        """Hover bobbing effect for Aether when sitting on the desktop."""
        if not self.dragging and not self.shaking and (self.current_state == "idle" or self.current_state == "ready"):
            self.bob_angle += 0.08
            offset = int(math.sin(self.bob_angle) * 5)
            self.move(self.base_x, self.base_y + offset)

    def start_processing(self, duration_ms=1500):
        """Plays processing animation, shakes screen and plays low growl audio."""
        if self.current_state == "processing":
            return
            
        self.current_state = "processing"
        self.shaking = True
        self.load_sprite()
        
        # Play asynchronous sound sweep
        SoundEffectThread("processing").start()
        
        # Start shake coordinates timer
        self.shake_timer.start(20)  # Shakes 50 times per second
        
        # Setup transformation timer to ready
        QTimer.singleShot(duration_ms, self.trigger_ready)

    def shake_aether(self):
        """Shakes the window coordinates randomly to simulate magical concentration."""
        if self.shaking:
            dx = random.randint(-4, 4)
            dy = random.randint(-4, 4)
            self.move(self.base_x + dx, self.base_y + dy)

    def trigger_ready(self):
        """Wakens Aether to Ready state!"""
        if self.current_state != "processing":
            return
            
        self.shake_timer.stop()
        self.shaking = False
        
        # Reset position to base
        self.move(self.base_x, self.base_y)
        
        self.current_state = "ready"
        self.load_sprite()
        
        # Play awakening sound
        SoundEffectThread("ready").start()


    def relax(self):
        """Returns Aether back to his baseline idle form."""
        self.shake_timer.stop()
        self.shaking = False
        
        if self.current_state == "idle":
            return
            
        self.move(self.base_x, self.base_y)
        self.current_state = "idle"
        self.load_sprite()
        
        # Reset visual styles
        self.setStyleSheet("")
        self.setWindowOpacity(0.95)
        
        # Play power down sweep
        SoundEffectThread("relax").start()

    # --- Mouse Drag-and-Drop Coordinates Handling ---
    
    def paintEvent(self, event):
        from PyQt5.QtGui import QPainter
        painter = QPainter(self)
        painter.setCompositionMode(QPainter.CompositionMode_Clear)
        painter.fillRect(self.rect(), Qt.transparent)
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        super().paintEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            self.dragging = True
            event.accept()
        elif event.button() == Qt.RightButton:
            self.show_context_menu(event.globalPos())

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.LeftButton and self.dragging:
            new_pos = event.globalPos() - self.drag_position
            self.move(new_pos)
            
            # Update base coordinates so bobbing occurs around new layout location
            self.base_x = new_pos.x()
            self.base_y = new_pos.y()
            
            self.moved.emit()
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.dragging = False
            # Recalibrate base coordinates
            self.base_x = self.x()
            self.base_y = self.y()
            self.clicked.emit()
            event.accept()

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.double_clicked.emit()
            event.accept()

    def enterEvent(self, event):
        self.hovering = True
        self.setWindowOpacity(1.0)
        if self.current_state == "idle":
            self.setStyleSheet("border: 1px dashed rgba(224, 159, 62, 0.4); border-radius: 8px;")
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.hovering = False
        if self.current_state == "idle":
            self.setWindowOpacity(0.95)
            self.setStyleSheet("")
        super().leaveEvent(event)

    def show_context_menu(self, pos):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #14181c;
                color: #fdf0d5;
                border: 2px solid #e09f3e;
                border-radius: 8px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #e09f3e;
                color: #14181c;
                font-weight: bold;
            }
        """)
        
        toggle_action = QAction("Open/Close Panel", self)
        toggle_action.triggered.connect(self.clicked.emit)
        
        action_text = "Toggle to Rest Form" if self.current_state in ("ready", "processing") else "Toggle to Ready Form"
        power_action = QAction(action_text, self)
        power_action.triggered.connect(self.toggle_ready_force)
        
        exit_action = QAction("Exit Assistant", self)
        exit_action.triggered.connect(self.close_app)
        
        menu.addAction(toggle_action)
        menu.addAction(power_action)
        menu.addSeparator()
        menu.addAction(exit_action)
        menu.exec_(pos)

    def toggle_ready_force(self):
        """Forces ready state manually via menu."""
        if self.current_state != "ready":
            self.start_processing()
        else:
            self.relax()

    def change_state(self, state: str):
        """State coordination from main script."""
        if state == "sleep":
            self.hide()
        elif state == "idle":
            self.show()
            self.relax()
        elif state == "active":
            self.show()
            self.start_processing()
