import ctypes
import time

# Windows Virtual Key Codes
VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF

def send_key_event(vk_code: int):
    """Sends a native Windows key press and release event."""
    # Key down
    ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)
    time.sleep(0.01)
    # Key up
    ctypes.windll.user32.keybd_event(vk_code, 0, 2, 0)

def change_volume(action: str) -> tuple[bool, str]:
    """
    Simulates keyboard volume commands to change master volume natively.
    action: "up", "down", "mute", "unmute"
    Returns (success, message).
    """
    action_clean = action.strip().lower()
    
    try:
        if action_clean == "mute" or action_clean == "unmute":
            # VK_VOLUME_MUTE toggles the mute state
            send_key_event(VK_VOLUME_MUTE)
            return True, f"I have toggled mute on your system volume!"
            
        elif action_clean == "up":
            # Send 5 volume up events (approx +10% volume)
            for _ in range(5):
                send_key_event(VK_VOLUME_UP)
                time.sleep(0.02)
            return True, "Volume increased! Hear the power!"
            
        elif action_clean == "down":
            # Send 5 volume down events (approx -10% volume)
            for _ in range(5):
                send_key_event(VK_VOLUME_DOWN)
                time.sleep(0.02)
            return True, "Volume turned down. Quiet as a training temple."
            
        else:
            return False, f"Unknown volume action: {action}"
            
    except Exception as e:
        return False, f"Failed to adjust volume: {str(e)}"
