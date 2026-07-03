import sqlite3
from datetime import datetime
from utils.config import DB_PATH

def get_connection():
    """Returns a connection to the SQLite database."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database and creates the necessary tables."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS task_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_type TEXT NOT NULL,
            query TEXT NOT NULL,
            response TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            status TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def add_task_log(task_type: str, query: str, response: str, status: str = "SUCCESS"):
    """Logs a completed task into the database."""
    # Ensure database is initialized
    init_db()
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # We use explicit current time in ISO format for easy reading
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute("""
        INSERT INTO task_history (task_type, query, response, timestamp, status)
        VALUES (?, ?, ?, ?, ?)
    """, (task_type, query, response, now, status))
    
    conn.commit()
    conn.close()

def get_recent_tasks(limit: int = 10):
    """Retrieves the recent task logs from the database."""
    init_db()
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, task_type, query, response, timestamp, status 
        FROM task_history 
        ORDER BY timestamp DESC 
        LIMIT ?
    """, (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    # Convert sqlite3.Row elements to dictionaries
    history_list = []
    for r in rows:
        history_list.append({
            "id": r["id"],
            "task_type": r["task_type"],
            "query": r["query"],
            "response": r["response"],
            "timestamp": r["timestamp"],
            "status": r["status"]
        })
    return history_list
