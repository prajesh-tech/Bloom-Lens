import os
from typing import Dict, Any
from app.core.logging import logger
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

            # Check if extracted text is insufficient (e.g., scanned PDF)
            if len(result["full_text"].strip()) < 50:
                logger.info(f"PDF text length ({len(result['full_text'].strip())}) insufficient. Invoking PaddleOCR fallback...")
                try:
                    ocr_result = OCRService.extract_text_from_scanned_pdf(file_path)
                    if len(ocr_result["full_text"].strip()) > len(result["full_text"].strip()):
                        return ocr_result
                except Exception as ocr_e:
                    logger.warning(f"OCR fallback encountered error, returning PyMuPDF result: {ocr_e}")

            return result

        else:
            raise ValueError(f"Unsupported file extension: {ext}")
