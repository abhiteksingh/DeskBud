import subprocess
import threading
import time

def show_native_toast(title: str, message: str):
    """
    Displays a native Windows Toast notification using PowerShell.
    This doesn't require any external Python packages and is highly reliable.
    """
    escaped_title = title.replace("'", "''")
    escaped_message = message.replace("'", "''")
    
    ps_script = f"""
    Add-Type -AssemblyName System.Windows.Forms
    [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
    $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
    $toastXml = [xml]$template.GetXml()
    $toastXml.GetElementsByTagName("text")[0].AppendChild($toastXml.CreateTextNode('{escaped_title}')) | Out-Null
    $toastXml.GetElementsByTagName("text")[1].AppendChild($toastXml.CreateTextNode('{escaped_message}')) | Out-Null
    $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
    $xml.LoadXml($toastXml.OuterXml)
    $toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
    [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Aether Desktop Companion").Show($toast)
    """
    
    try:
        subprocess.Popen(
            ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps_script],
            creationflags=subprocess.CREATE_NO_WINDOW
        )
    except Exception as e:
        print(f"Failed to trigger toast notification: {str(e)}")

def reminder_worker(delay_seconds: float, message: str):
    """Worker function that runs in a separate thread, sleeps, and sends the notification."""
    time.sleep(delay_seconds)
    show_native_toast("Aether Reminder", message)

def set_reminder(minutes: float, message: str) -> tuple[bool, str]:
    """
    Schedules a reminder for the given number of minutes.
    Returns (success, user_message).
    """
    if minutes <= 0:
        return False, "Please specify a positive time duration for the reminder."
        
    delay_seconds = minutes * 60.0
    
    # Spawn background thread to handle the sleep and notification
    t = threading.Thread(
        target=reminder_worker, 
        args=(delay_seconds, message),
        daemon=True
    )
    t.start()
    
    # Format a friendly response
    if minutes < 1:
        seconds = int(minutes * 60)
        time_str = f"{seconds} seconds"
    else:
        # Check if it has decimal or is a round number
        if minutes == int(minutes):
            time_str = f"{int(minutes)} minute" + ("s" if minutes > 1 else "")
        else:
            time_str = f"{minutes:.1f} minutes"
            
    return True, f"Alright! I've set a reminder. I will remind you in {time_str} to: '{message}'"
