import os
from typing import Dict, Any
from app.core.logging import logger
from app.core.config import settings
from app.services.pdf_service import PDFService
from app.services.docx_service import DOCXService
from app.services.ocr_service import OCRService


class DocumentService:
    """
    Common Document Processing Abstraction.
    Provides unified interface for PDF, DOCX, and OCR document text extraction.
    """

    @staticmethod
    def process_document(file_path: str) -> Dict[str, Any]:
        """
        Extracts structured document text regardless of source file format.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".docx":
            logger.info(f"Processing DOCX document: {file_path}")
            return DOCXService.extract_text_from_docx(file_path)

        elif ext == ".pdf":
            logger.info(f"Processing PDF document: {file_path}")
            result = PDFService.extract_text_from_pdf(file_path)

            low_text_pages = [page["page_number"] for page in result["pages"]
                              if len(page["text"].strip()) < settings.OCR_MIN_TEXT_CHARS]
            if low_text_pages:
                try:
                    ocr_result = OCRService.extract_text_from_scanned_pdf(file_path, page_numbers=low_text_pages)
                    replacements = {page["page_number"]: page["text"] for page in ocr_result["pages"]}
                    changed = False
                    for page in result["pages"]:
                        replacement = replacements.get(page["page_number"], "")
                        if len(replacement.strip()) > len(page["text"].strip()):
                            page["text"] = replacement
                            changed = True
                    if changed:
                        result["full_text"] = "\n\n".join(page["text"] for page in result["pages"] if page["text"])
                        result["extraction_method"] = "pdf_pymupdf+ocr_paddle"
                except Exception:
                    logger.warning("Per-page OCR failed; retaining extracted PDF text")

            return result

        else:
            raise ValueError(f"Unsupported file extension: {ext}")
