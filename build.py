import os
import sys
import subprocess
import shutil

def main():
    print("=== Aether Desktop Companion Builder ===")
    
    # 1. Install pyinstaller if not present
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller not found. Installing via pip...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        
    print("Preparing build folders...")
    # Clear previous build/dist folders
    for folder in ["build", "dist"]:
        if os.path.exists(folder):
            try:
                shutil.rmtree(folder)
            except Exception as e:
                print(f"Warning: Could not clear existing folder {folder}: {e}")
            
    # 2. Run PyInstaller command
    # We build with --onedir for fast startup, and --noconsole to hide cmd window.
    # We run as python -m PyInstaller to bypass PATH variable issues on Windows.
    pyinstaller_cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconsole",
        "--onedir",
        "--add-data", "ui/assets;ui/assets",
        "--icon", "ui/assets/aether_icon.ico",
        "--name", "AetherCompanion",
        "main.py"
    ]
    
    print(f"Running command: {' '.join(pyinstaller_cmd)}")
    try:
        subprocess.check_call(pyinstaller_cmd)
        print("\nBuild successful! Binary folder is located in: dist/AetherCompanion/")
        print("You can run the application by launching 'dist/AetherCompanion/AetherCompanion.exe'\n")
    except subprocess.CalledProcessError as e:
        print(f"\nBuild failed with exit code: {e.returncode}")
        sys.exit(1)

if __name__ == "__main__":
    main()
