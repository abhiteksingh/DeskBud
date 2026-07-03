import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory of the Project
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
env_path = BASE_DIR / '.env'
load_dotenv(dotenv_path=env_path)

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# SQLite Database Location
DB_PATH = Path.home() / ".aether" / "history.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# Assets Directory
ASSETS_DIR = BASE_DIR / "ui" / "assets"
AETHER_IDLE_PATH = ASSETS_DIR / "aether_idle.png"
AETHER_READY_PATH = ASSETS_DIR / "aether_ready.png"
AETHER_CHARGING_PATH = ASSETS_DIR / "aether_charging.png"


# File finder settings (Default directories to search)
USER_HOME = Path.home()
SEARCH_DIRECTORIES = [
    BASE_DIR,
    USER_HOME / "Desktop",
    USER_HOME / "Documents",
    USER_HOME / "Downloads"
]

# Supported File Types for Summarization
SUPPORTED_DOC_EXTENSIONS = {'.txt', '.pdf', '.docx'}
