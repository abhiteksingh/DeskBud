import ctypes
import time
import threading

class RECT(ctypes.Structure):
    _fields_ = [
        ('left', ctypes.c_long),
        ('top', ctypes.c_long),
        ('right', ctypes.c_long),
        ('bottom', ctypes.c_long)
    ]

class SleepDetector(threading.Thread):
    def __init__(self, callback, check_interval_sec: float = 2.0):
        """
        Background thread that checks if a fullscreen window is in focus.
        Calls callback(is_fullscreen=True/False) on state change.
        """
        super().__init__()
        self.callback = callback
        self.check_interval = check_interval_sec
        self.daemon = True
        self.is_fullscreen_active = False
        self._stop_event = threading.Event()
        
        # Windows API Setup
        self.user32 = ctypes.windll.user32
        
    def stop(self):
        self._stop_event.set()
        
    def run(self):
        while not self._stop_event.is_set():
            try:
                current_state = self.check_fullscreen()
                if current_state != self.is_fullscreen_active:
                    self.is_fullscreen_active = current_state
                    self.callback(self.is_fullscreen_active)
            except Exception as e:
                print(f"Error in SleepDetector: {str(e)}")
            time.sleep(self.check_interval)

    def check_fullscreen(self) -> bool:
        """Checks if the foreground window is in fullscreen mode."""
        hwnd = self.user32.GetForegroundWindow()
        if not hwnd:
            return False
            
        # Get class name of foreground window to avoid falsely sleeping on desktop clicks
        buf = ctypes.create_unicode_buffer(256)
        self.user32.GetClassNameW(hwnd, buf, 256)
        class_name = buf.value
        
        if class_name in ("Progman", "WorkerW", "Shell_TrayWnd"):
            return False
            
        # Get active window rect
        rect = RECT()
        if not self.user32.GetWindowRect(hwnd, ctypes.byref(rect)):
            return False
            
        # Get the screen size of the monitor containing the window
        # For simplicity and robust fallback, check if it matches the primary screen first.
        # Alternatively, we can use MonitorFromWindow for multi-monitor setups.
        MONITOR_DEFAULTTONEAREST = 2
        monitor = self.user32.MonitorFromWindow(hwnd, MONITOR_DEFAULTTONEAREST)
        
        # Get monitor info structure
        # MonitorInfo struct has cbSize, rcMonitor, rcWork, dwFlags
        # rcMonitor is a RECT struct
        class MONITORINFO(ctypes.Structure):
            _fields_ = [
                ('cbSize', ctypes.c_ulong),
                ('rcMonitor', RECT),
                ('rcWork', RECT),
                ('dwFlags', ctypes.c_ulong)
            ]
            
        monitor_info = MONITORINFO()
        monitor_info.cbSize = ctypes.sizeof(MONITORINFO)
        
        if self.user32.GetMonitorInfoW(monitor, ctypes.byref(monitor_info)):
            m_rect = monitor_info.rcMonitor
            
            # Compare window rect with monitor rect
            # Fullscreen apps cover the entire monitor area (rcMonitor)
            is_covering_width = rect.left <= m_rect.left and rect.right >= m_rect.right
            is_covering_height = rect.top <= m_rect.top and rect.bottom >= m_rect.bottom
            
            if is_covering_width and is_covering_height:
                # Also verify the window style is indeed a fullscreen-like window (no border or caption)
                GWL_STYLE = -16
                WS_CAPTION = 0x00C00000
                style = self.user32.GetWindowLongW(hwnd, GWL_STYLE)
                # If it has a title bar/caption, it's just a maximized window, not fullscreen.
                if style & WS_CAPTION == 0:
                    return True
                    
        return False
