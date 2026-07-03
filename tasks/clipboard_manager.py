import sqlite3
import pyperclip
from datetime import datetime
from utils.config import DB_PATH

def get_db_connection():
    """Returns a connection to the SQLite database."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_clipboard_db():
    """Initializes the clipboard history table in the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clipboard_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def log_clipboard_change() -> bool:
    """
    Checks the current system clipboard. If it contains new text content 
    that differs from the last stored item, logs it to SQLite.
    Returns True if a new item was logged.
    """
    try:
        current_clip = pyperclip.paste().strip()
    except Exception:
        return False
        
    if not current_clip:
        return False
        
    # Ensure database table is created
    init_clipboard_db()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Query the last logged clipboard entry
    cursor.execute("""
        SELECT content FROM clipboard_history 
        ORDER BY id DESC LIMIT 1
    """)
    last_row = cursor.fetchone()
    
    # If the text is the same as the last logged entry, skip logging to avoid duplicates
    if last_row and last_row["content"] == current_clip:
        conn.close()
        return False
        
    # Log the new clipboard entry
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO clipboard_history (content, timestamp)
        VALUES (?, ?)
    """, (current_clip, now))
    
    conn.commit()
    conn.close()
    return True

def get_clipboard_history(limit: int = 5) -> list[dict]:
    """Retrieves the recent clipboard history items from the database."""
    init_clipboard_db()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT content, timestamp FROM clipboard_history 
        ORDER BY id DESC LIMIT ?
    """, (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [{"content": r["content"], "timestamp": r["timestamp"]} for r in rows]

def format_clipboard_history(items: list[dict]) -> str:
    """Formats the list of clipboard items into a readable response."""
    if not items:
        return "You haven't copied any text yet since Aether started watching over you!"
        
    result_lines = ["Here are the items you copied earlier:"]
    for i, item in enumerate(items, 1):
        content_preview = item["content"]
        # Truncate long lines to keep the HUD clean
        if len(content_preview) > 60:
            content_preview = content_preview[:57] + "..."
        # Replace newlines with spaces for preview
        content_preview = content_preview.replace("\n", " ").replace("\r", "")
        
        result_lines.append(f"{i}. \"{content_preview}\"")
        
    return "\n".join(result_lines)
