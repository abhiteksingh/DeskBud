import os
from pathlib import Path
from tasks.file_finder import find_files

def search_file_for_deletion(query: str) -> dict:
    """
    Searches for a file matching the query.
    Returns a dict indicating search results:
    {
      "status": "NOT_FOUND" | "AMBIGUOUS" | "FOUND",
      "matches": list of matches,
      "file_path": str (only if FOUND),
      "file_name": str (only if FOUND)
    }
    """
    matches = find_files(query, limit=5)
    if not matches:
        return {"status": "NOT_FOUND", "matches": []}
    elif len(matches) > 1:
        return {"status": "AMBIGUOUS", "matches": matches}
    else:
        match = matches[0]
        return {
            "status": "FOUND",
            "matches": matches,
            "file_path": match["path"],
            "file_name": match["name"]
        }

def delete_file_path(path_str: str) -> tuple[bool, str]:
    """Deletes the file permanently at the specified path."""
    try:
        path = Path(path_str)
        if not path.exists():
            return False, f"The scroll at {path_str} no longer exists in the realm."
            
        if path.is_dir():
            return False, "Banishment of directories is currently locked. I can only banish single files."
            
        os.remove(path)
        return True, f"Banishment complete! '{path.name}' has been cast into the void."
    except Exception as e:
        return False, f"An obstacle prevented the deletion: {str(e)}"
