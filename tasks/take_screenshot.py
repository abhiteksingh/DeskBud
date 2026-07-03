import os
import time
from pathlib import Path
from PyQt5.QtWidgets import QApplication

def capture_screenshot() -> tuple[bool, str]:
    """Captures the primary screen, saves it to the Pictures/Downloads folder, and opens it."""
    try:
        screen = QApplication.primaryScreen()
        if not screen:
            return False, "The screen viewport is not accessible to my magic."
            
        dest_dir = Path.home() / "Pictures"
        if not dest_dir.exists():
            dest_dir = Path.home() / "Downloads"
            
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        file_path = dest_dir / filename
        
        # Grab the full desktop screen (window ID 0)
        pixmap = screen.grabWindow(0)
        success = pixmap.save(str(file_path), "PNG")
        
        if success:
            # Auto-open using system default viewer
            os.startfile(str(file_path))
            return True, f"Behold! I have captured your screen and inscribed it into '{filename}' in your Pictures folder."
        else:
            return False, "I was unable to serialize the screen image."
    except Exception as e:
        return False, f"Screenshot error: {str(e)}"
