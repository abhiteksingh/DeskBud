from pathlib import Path
from pypdf import PdfReader
import docx

def extract_text_from_file(file_path_str: str, max_chars: int = 15000) -> tuple[bool, str]:
    """
    Extracts text from txt, pdf, or docx files.
    Returns (success, text_or_error_message).
    """
    path = Path(file_path_str)
    if not path.exists():
        return False, f"File does not exist at '{file_path_str}'"
        
    ext = path.suffix.lower()
    
    try:
        if ext == '.txt':
            # Try reading with UTF-8 first, fallback to cp1252 (standard Windows)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read(max_chars)
                return True, content
            except UnicodeDecodeError:
                with open(path, 'r', encoding='cp1252') as f:
                    content = f.read(max_chars)
                return True, content
                
        elif ext == '.pdf':
            reader = PdfReader(path)
            text_parts = []
            char_count = 0
            
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
                    char_count += len(page_text)
                    if char_count >= max_chars:
                        break
                        
            full_text = "\n".join(text_parts)[:max_chars]
            if not full_text.strip():
                return False, "This PDF appears to be empty or contains scanned images (OCR needed)."
            return True, full_text
            
        elif ext == '.docx':
            doc = docx.Document(path)
            text_parts = []
            char_count = 0
            
            for para in doc.paragraphs:
                if para.text:
                    text_parts.append(para.text)
                    char_count += len(para.text)
                    if char_count >= max_chars:
                        break
                        
            full_text = "\n".join(text_parts)[:max_chars]
            if not full_text.strip():
                return False, "This Word document is empty."
            return True, full_text
            
        else:
            return False, f"Unsupported file type '{ext}'. Aether only supports txt, pdf, and docx files."
            
    except Exception as e:
        return False, f"Error reading file: {str(e)}"
