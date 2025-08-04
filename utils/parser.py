import pdfplumber
import docx
import os
from fastapi import UploadFile
from typing import Union
import io

async def parse_file(file: UploadFile) -> Union[str, None]:
    content = ""
    filename = (file.filename or "").lower()

    if filename.endswith(".pdf"):
        content = await parse_pdf(file)
    elif filename.endswith(".docx"):
        content = await parse_docx(file)
    elif filename.endswith(".txt"):
        content = await file.read()
        content = content.decode("utf-8")
    else:
        return None

    return content.strip()

async def parse_pdf(file: UploadFile) -> str:
    text = ""
    file_bytes = await file.read()
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

async def parse_docx(file: UploadFile) -> str:
    # Ensure the file is seekable by reading into a BytesIO object
    file.file.seek(0)
    content = io.BytesIO(file.file.read())
    doc = docx.Document(content)
    return "\n".join([para.text for para in doc.paragraphs])