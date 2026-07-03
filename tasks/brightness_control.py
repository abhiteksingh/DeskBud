import subprocess

def get_current_brightness() -> int:
    """Queries WMI for the current monitor brightness. Returns percentage (0-100)."""
    ps_cmd = "Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorBrightness | Select-Object -ExpandProperty CurrentBrightness"
    try:
        res = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_cmd], 
            capture_output=True, 
            text=True, 
            timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        if res.returncode == 0 and res.stdout.strip():
            return int(res.stdout.strip())
    except Exception:
        pass
    return -1

def set_brightness_percent(percent: int) -> bool:
    """Invokes WMI WmiSetBrightness method to change brightness level."""
    percent = max(0, min(100, percent))
    ps_cmd = f"Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorBrightnessMethods | Invoke-CimMethod -MethodName WmiSetBrightness -Arguments @{{Timeout=0; Brightness={percent}}}"
    try:
        res = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_cmd],
            capture_output=True,
            timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        return res.returncode == 0
    except Exception:
        return False

def adjust_brightness(action: str, value: int = None) -> tuple[bool, str]:
    """
    Adjusts brightness based on requested action.
    action: "up", "down", "set"
    value: absolute target percentage if action is "set"
    """
    action_clean = action.strip().lower()
    current = get_current_brightness()
    
    if current == -1:
        return False, "WMI brightness controls are only supported on laptops or displays with active WMI driver support!"
        
    try:
        if action_clean == "set":
            if value is None:
                return False, "No brightness percentage value specified."
            target = max(0, min(100, value))
            if set_brightness_percent(target):
                return True, f"I have set your screen brightness to {target}%!"
            return False, "Failed to apply screen brightness settings."
            
        elif action_clean == "up":
            target = min(100, current + 15)
            if set_brightness_percent(target):
                return True, f"Solar Flare! Brightness increased to {target}%!"
            return False, "Failed to increase screen brightness."
            
        elif action_clean == "down":
            target = max(0, current - 15)
            if set_brightness_percent(target):
                return True, f"Solar Eclipse! Brightness decreased to {target}%!"
            return False, "Failed to decrease screen brightness."
            
        else:
            return False, f"Unknown brightness action: {action}"
            
    except Exception as e:
        return False, f"Failed to adjust brightness: {str(e)}"
