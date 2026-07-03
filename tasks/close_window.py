import ctypes

def close_active_window() -> tuple[bool, str]:
    """
    Identifies the active foreground window and sends a native WM_CLOSE 
    message to shut it down cleanly.
    Returns (success, message).
    """
    WM_CLOSE = 0x0010
    
    try:
        # Get active window handle
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        if not hwnd:
            return False, "I couldn't detect any active window to close!"
            
        # Retrieve the window title to include in Aether's response
        buf = ctypes.create_unicode_buffer(512)
        ctypes.windll.user32.GetWindowTextW(hwnd, buf, 512)
        window_title = buf.value.strip()
        
        # Send post message to close window
        ctypes.windll.user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
        
        display_name = f"'{window_title}'" if window_title else "the active window"
        return True, f"Haaaa! I've closed {display_name}!"
        
    except Exception as e:
        return False, f"Failed to close active window: {str(e)}"
