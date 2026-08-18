import os
import tempfile
import pytest
import fitz
import docx
from app.services.pdf_service import PDFService
from app.services.docx_service import DOCXService
from app.services.document_service import DocumentService


def create_sample_pdf(file_path: str, text_content: str):
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), text_content)
    doc.save(file_path)
    doc.close()


def create_sample_docx(file_path: str, text_content: str):
    doc = docx.Document()
    doc.add_paragraph(text_content)
    doc.save(file_path)


@pytest.mark.asyncio
async def test_pdf_text_extraction():
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        create_sample_pdf(tmp.name, "Q1. Explain database normalization. [5 Marks]")
        tmp_path = tmp.name

    try:
        res = PDFService.extract_text_from_pdf(tmp_path)
        assert "Q1. Explain database normalization." in res["full_text"]
        assert res["page_count"] == 1
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@pytest.mark.asyncio
async def test_docx_text_extraction():
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
        create_sample_docx(tmp.name, "Q2. Define ACID properties in DBMS. [10 Marks]")
        tmp_path = tmp.name

    try:
        res = DOCXService.extract_text_from_docx(tmp_path)
        assert "Q2. Define ACID properties in DBMS." in res["full_text"]
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@pytest.mark.asyncio
async def test_document_service_abstraction():
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
        create_sample_docx(tmp.name, "Q3. Apply 3NF to relation R.")
        tmp_path = tmp.name

    try:
        res = DocumentService.process_document(tmp_path)
        assert "Apply 3NF" in res["full_text"]
        assert res["extraction_method"] == "docx_python_docx"
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
