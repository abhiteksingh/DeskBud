import ctypes

def minimize_all_windows() -> tuple[bool, str]:
    """
    Minimizes all open windows on the screen natively using Windows keybd_event.
    This simulates pressing Win + M to clear the desktop instantaneously.
    Returns (success, message).
    """
    VK_LWIN = 0x5B
    VK_M = 0x4D
    KEYEVENTF_KEYUP = 0x0002
    
    try:
        # Press left Windows key
        ctypes.windll.user32.keybd_event(VK_LWIN, 0, 0, 0)
        # Press M key
        ctypes.windll.user32.keybd_event(VK_M, 0, 0, 0)
        # Release M key
        ctypes.windll.user32.keybd_event(VK_M, 0, KEYEVENTF_KEYUP, 0)
        # Release left Windows key
        ctypes.windll.user32.keybd_event(VK_LWIN, 0, KEYEVENTF_KEYUP, 0)
        
        return True, "Haaaa! Minimizing everything! Your desktop is clear!"
    except Exception as e:
        return False, f"Failed to minimize windows: {str(e)}"
