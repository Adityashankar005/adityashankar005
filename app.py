from PyPDF2 import PdfReader
import re

def extract_paragraphs_from_pdf_bytes(pdf_bytes):
    paragraphs = []
    reader = PdfReader(io.BytesIO(pdf_bytes))

    full_text = ""
    for page in reader.pages:
        text = page.extract_text() or ""
        full_text += "\n" + text

    raw_pars = re.split(r'\n{2,}', full_text)
    for p in raw_pars:
        p = p.strip()
        if p:
            paragraphs.append(p)

    return paragraphs
