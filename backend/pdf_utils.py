"""
pdf_utils.py
------------
Plain text extraction from uploaded complaint PDFs (e.g. a scanned-looking
but actually text-based "customer complaint report"). Per the assignment
brief, production-grade OCR is explicitly NOT required - this handles
text-based PDFs, which is enough to demo the "upload a PDF -> Copilot
extracts fields" flow shown in the reference video.
"""
from io import BytesIO
from pypdf import PdfReader


def extract_text_from_pdf(file_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(file_bytes))
    pages_text = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages_text).strip()
