import ctypes

def lock_workstation() -> tuple[bool, str]:
    """Locks the Windows workstation screen using native Win32 API."""
    try:
        ctypes.windll.user32.LockWorkStation()
        return True, "By the ancient dragons, the screen is locked! Your sanctuary is protected."
    except Exception as e:
        return False, f"Failed to lock screen: {str(e)}"
