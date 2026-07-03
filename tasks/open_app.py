import os
import difflib
from pathlib import Path

def get_installed_apps():
    """
    Scans the system for installed applications by retrieving shortcuts (.lnk) 
    from start menu directories and desktop folders, and returns a dictionary 
    mapping lowercase app names to their file paths.
    """
    apps = {}
    
    # Common locations for application shortcuts (.lnk files)
    user_profile = os.environ.get("USERPROFILE", "")
    start_menu_paths = [
        Path(os.environ.get("ProgramData", "C:\\ProgramData")) / "Microsoft\\Windows\\Start Menu\\Programs",
        Path(user_profile) / "AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs",
        Path(user_profile) / "Desktop",
        Path("C:\\Users\\Public\\Desktop")
    ]
    
    # Scan for shortcut (.lnk) files
    for path in start_menu_paths:
        if path.exists():
            for root, _, files in os.walk(path):
                for file in files:
                    if file.lower().endswith(".lnk"):
                        app_name = file[:-4]  # Remove .lnk
                        app_path = Path(root) / file
                        apps[app_name.lower()] = str(app_path)
                        
    # Let's also include some common executables directly in typical paths with depth=2 limit
    common_install_dirs = [
        Path("C:\\Program Files"),
        Path("C:\\Program Files (x86)"),
        Path(user_profile) / "AppData\\Local\\Programs"
    ]
    
    for base_dir in common_install_dirs:
        if base_dir.exists():
            try:
                # Direct subdirectories (depth 1)
                for entry in base_dir.iterdir():
                    if entry.is_dir():
                        # Look for .exe files directly inside the subdirectory (depth 2)
                        try:
                            for sub_entry in entry.iterdir():
                                if sub_entry.is_file() and sub_entry.name.lower().endswith(".exe"):
                                    exe_name = sub_entry.stem
                                    # Do not overwrite if shortcut already exists to prioritize shortcuts
                                    if exe_name.lower() not in apps:
                                        apps[exe_name.lower()] = str(sub_entry)
                        except (PermissionError, FileNotFoundError):
                            continue
            except (PermissionError, FileNotFoundError):
                continue
                
    # Add manual fallbacks for common apps if not found
    fallbacks = {
        "notepad": "notepad.exe",
        "calc": "calc.exe",
        "calculator": "calc.exe",
        "explorer": "explorer.exe",
        "cmd": "cmd.exe",
        "powershell": "powershell.exe",
        "chrome": "chrome.exe",
        "firefox": "firefox.exe",
        "edge": "msedge.exe",
        "msedge": "msedge.exe"
    }
    for name, path in fallbacks.items():
        if name not in apps:
            apps[name] = path

    return apps

def launch_app(app_query: str) -> tuple[bool, str]:
    """
    Finds and launches an application matching the query.
    Returns (success, message).
    """
    app_query_clean = app_query.strip().lower()
    if not app_query_clean:
        return False, "Application name cannot be empty."
        
    apps = get_installed_apps()
    
    # 1. Try exact match
    if app_query_clean in apps:
        app_path = apps[app_query_clean]
        try:
            os.startfile(app_path)
            return True, f"Successfully opened {app_query}."
        except Exception as e:
            return False, f"Failed to start {app_query}: {str(e)}"
            
    # 2. Try substring match (e.g. "code" -> "visual studio code")
    matches = [name for name in apps if app_query_clean in name]
    if matches:
        # Sort matches by length so the closest length match is chosen
        matches.sort(key=len)
        best_match = matches[0]
        try:
            os.startfile(apps[best_match])
            # Return proper display name (original case or capitalized match)
            return True, f"Successfully opened {best_match.title()}."
        except Exception as e:
            return False, f"Failed to start {best_match}: {str(e)}"
            
    # 3. Try fuzzy matching
    close_matches = difflib.get_close_matches(app_query_clean, list(apps.keys()), n=1, cutoff=0.5)
    if close_matches:
        best_match = close_matches[0]
        try:
            os.startfile(apps[best_match])
            return True, f"Successfully opened {best_match.title()}."
        except Exception as e:
            return False, f"Failed to start {best_match}: {str(e)}"
            
    # 4. Final attempt: execute command via shell (e.g. user typed "notepad" or "calc" or "explorer")
    try:
        os.startfile(app_query_clean)
        return True, f"Sent start command for {app_query_clean}."
    except Exception:
        pass
        
    return False, f"Could not find or open any application matching '{app_query}'."

if __name__ == "__main__":
    # Test execution
    success, msg = launch_app("chrome")
    print(msg)
