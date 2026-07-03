import pyperclip

def copy_draft_to_clipboard(text: str) -> tuple[bool, str]:
    """
    Copies the drafted text to the system clipboard using pyperclip.
    Returns (success, message).
    """
    cleaned_text = text.strip()
    if not cleaned_text:
        return False, "Failed to copy: draft text is empty."
        
    try:
        pyperclip.copy(cleaned_text)
        return True, "I have drafted the text and copied it to your clipboard. You can press Ctrl+V to paste it anywhere!"
    except Exception as e:
        return False, f"Failed to copy to clipboard: {str(e)}"
