from typing import Dict, Any, List
import docx
from docx.text.paragraph import Paragraph
from docx.table import Table
from app.core.logging import logger
from app.utils.text_cleaner import clean_text


class DOCXService:
    """Service for extracting text from Microsoft Word DOCX question papers."""

    @staticmethod
    def extract_text_from_docx(file_path: str) -> Dict[str, Any]:
        """
        Extracts structured text from DOCX paragraphs and tables.
        """
        paragraphs_text: List[str] = []

        try:
            doc = docx.Document(file_path)

            for element in doc.element.body.iterchildren():
                if element.tag.endswith("}p"):
                    text = clean_text(Paragraph(element, doc).text)
                    if text:
                        paragraphs_text.append(text)
                elif element.tag.endswith("}tbl"):
                    for row in Table(element, doc).rows:
                        texts = [clean_text(cell.text) for cell in row.cells if clean_text(cell.text)]
                        if texts:
                            paragraphs_text.append(" | ".join(texts))

            full_text = "\n\n".join(paragraphs_text)
            logger.info(f"Extracted {len(full_text)} characters from DOCX: {file_path}")

            return {
                "pages": [{"page_number": 1, "text": full_text}],
                "full_text": full_text,
                "page_count": None,
                "extraction_method": "docx_python_docx"
            }
        except Exception as e:
            logger.error(f"Error extracting text from DOCX {file_path}: {e}")
            raise RuntimeError(f"Failed to process DOCX file: {str(e)}")
