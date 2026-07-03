import os
from pathlib import Path
from utils.config import SEARCH_DIRECTORIES

# Directory names we should ignore during search for efficiency and security
EXCLUDE_DIRS = {
    "node_modules", ".git", ".github", ".gemini", "__pycache__", 
    "env", "venv", ".venv", "appdata", "local settings", "temp", "tmp"
}

def find_files(query: str, limit: int = 5) -> list[dict]:
    """
    Searches config.SEARCH_DIRECTORIES for files whose names contain the query.
    Returns a list of dictionaries with file details: {'name', 'path', 'size', 'modified'}.
    """
    query_lower = query.strip().lower()
    if not query_lower:
        return []
        
    matches = []
    
    for search_dir in SEARCH_DIRECTORIES:
        if not search_dir.exists():
            continue
            
        try:
            for root, dirs, files in os.walk(search_dir):
                # Filter out excluded directories in-place to avoid traversing them
                dirs[:] = [d for d in dirs if d.lower() not in EXCLUDE_DIRS and not d.startswith('.')]
                
                for file in files:
                    if query_lower in file.lower():
                        file_path = Path(root) / file
                        try:
                            stat = file_path.stat()
                            matches.append({
                                "name": file,
                                "path": str(file_path),
                                "size_bytes": stat.st_size,
                                "modified_time": stat.st_mtime
                            })
                            # If we hit a large number of matches, stop searching this folder
                            if len(matches) >= limit * 3:
                                break
                        except (PermissionError, FileNotFoundError):
                            continue
                if len(matches) >= limit * 3:
                    break
        except Exception:
            continue
            
    # Sort matches by how close the query is to the filename or query string length
    # A perfect match or prefix gets higher priority
    def sort_key(item):
        name = item["name"].lower()
        # Prefer exact match
        if name == query_lower:
            return (0, len(name))
        # Prefer startswith
        if name.startswith(query_lower):
            return (1, len(name))
        # fallback
        return (2, len(name))
        
    matches.sort(key=sort_key)
    return matches[:limit]

def open_file_or_dir(path_str: str) -> tuple[bool, str]:
    """Opens the specified file or folder using Windows shell."""
    try:
        path = Path(path_str)
        if path.exists():
            os.startfile(str(path))
            return True, f"Opened {path.name}."
        return False, "File does not exist."
    except Exception as e:
        return False, f"Failed to open file: {str(e)}"

def format_file_result(matches: list[dict]) -> str:
    """Formats the list of file matches as a readable string."""
    if not matches:
        return "No matching files found."
        
    result_lines = ["I found these files:"]
    for i, item in enumerate(matches, 1):
        path = Path(item["path"])
        # Format size in KB or MB
        size_kb = item["size_bytes"] / 1024
        size_str = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb/1024:.1f} MB"
        result_lines.append(f"{i}. {item['name']} ({size_str}) - {path.parent}")
        
    return "\n".join(result_lines)
