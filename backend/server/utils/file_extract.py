import os
from PyPDF2 import PdfReader
from io import BytesIO

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from a PDF file."""
    try:
        reader = PdfReader(BytesIO(file_bytes))
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text.strip()
    except Exception as e:
        print(f"Error extracting PDF: {e}")
        return ""

def extract_text_from_txt(file_bytes: bytes) -> str:
    """Extract text from a TXT file."""
    try:
        return file_bytes.decode("utf-8")
    except Exception as e:
        print(f"Error extracting TXT: {e}")
        return ""

def extract_text_from_image(file_bytes: bytes) -> str:
    """
    Extract text from an image.
    Requires pytesseract to be installed on the system.
    Placeholder if taking too much setup, but implemented here conceptually.
    """
    try:
        from PIL import Image
        import pytesseract
        
        image = Image.open(BytesIO(file_bytes))
        text = pytesseract.image_to_string(image)
        return text.strip()
    except ImportError:
        return "[Image text extraction requires pytesseract to be installed.]"
    except Exception as e:
        print(f"Error extracting Image: {e}")
        return ""
