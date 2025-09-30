# evaluator/utils.py
from PyPDF2 import PdfReader
import docx
import os

def read_uploaded_file_text(filefield):
    if not filefield:
        return ""
    path = filefield.path
    name = path.lower()
    try:
        if name.endswith(".txt"):
            return open(path, "r", encoding="utf-8", errors="ignore").read()
        if name.endswith(".pdf"):
            r = PdfReader(path)
            texts = [p.extract_text() or "" for p in r.pages]
            return "\n".join(texts)
        if name.endswith(".docx"):
            doc = docx.Document(path)
            return "\n".join(p.text for p in doc.paragraphs)
    except Exception as e:
        return f"[error reading file: {e}]"
    return ""
