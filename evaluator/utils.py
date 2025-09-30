# evaluator/utils.py
import os
from PyPDF2 import PdfReader
import docx


def _read_txt(path: str) -> str:
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read()


def _read_pdf(path: str) -> str:
    reader = PdfReader(path)
    return '\n'.join(page.extract_text() or '' for page in reader.pages)


def _read_docx(path: str) -> str:
    doc = docx.Document(path)
    return '\n'.join(p.text for p in doc.paragraphs)


def read_uploaded_file_text(filefield) -> str:
    """
    Extract text content from an uploaded file (txt, pdf, docx).
    Returns empty string if file is missing or unsupported.
    """
    if not filefield:
        return ''

    path = filefield.path
    _, ext = os.path.splitext(path.lower())

    try:
        if ext == '.txt':
            return _read_txt(path)
        elif ext == '.pdf':
            return _read_pdf(path)
        elif ext == '.docx':
            return _read_docx(path)
    except Exception:
        # Could log error here for debugging
        return ''

    # Unsupported extension
    return ''
