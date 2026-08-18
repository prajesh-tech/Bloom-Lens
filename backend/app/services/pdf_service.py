from typing import Dict, Any, List
import fitz  # PyMuPDF
from app.core.logging import logger
from app.utils.text_cleaner import clean_text


class PDFService:
    """Service for extracting text from PDF question papers using PyMuPDF."""

    @staticmethod
    def extract_text_from_pdf(file_path: str) -> Dict[str, Any]:
        """
        Extracts structured page-by-page text from PDF document.
        Returns pages list, full_text string, and page count.
        """
        pages: List[Dict[str, Any]] = []
        full_text_parts: List[str] = []

        try:
            doc = fitz.open(file_path)
            for page_num, page in enumerate(doc, start=1):
                page_text = clean_text(page.get_text("text"))
                pages.append({
                    "page_number": page_num,
                    "text": page_text
                })
                if page_text:
                    full_text_parts.append(page_text)
            doc.close()

            full_text = "\n\n".join(full_text_parts)
            logger.info(f"Extracted {len(full_text)} characters across {len(pages)} pages from PDF: {file_path}")

            return {
                "pages": pages,
                "full_text": full_text,
                "page_count": len(pages),
                "extraction_method": "pdf_pymupdf"
            }
        except Exception as e:
            logger.error(f"Error extracting text from PDF {file_path}: {e}")
            raise RuntimeError(f"Failed to process PDF file: {str(e)}")
