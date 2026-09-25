import threading
from typing import Dict, Any, List
import fitz  # PyMuPDF
from app.core.config import settings
from app.core.logging import logger
from app.utils.text_cleaner import clean_text

_ocr_engine = None
_ocr_lock = threading.Lock()


def get_ocr_engine():
    """Lazily initializes PaddleOCR engine to preserve startup speed with double-checked lock."""
    global _ocr_engine
    if _ocr_engine is not None:
        return _ocr_engine if _ocr_engine is not False else None
    with _ocr_lock:
        if _ocr_engine is None:
            try:
                import warnings
                from paddleocr import PaddleOCR
                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore", category=DeprecationWarning)
                    _ocr_engine = PaddleOCR(use_angle_cls=True, lang=settings.OCR_LANG, show_log=False)
                logger.info("PaddleOCR engine initialized successfully.")
            except Exception as e:
                logger.warning(f"PaddleOCR engine failed to initialize: {e}")
                _ocr_engine = False
    return _ocr_engine if _ocr_engine is not False else None


class OCRService:
    """Service for optical character recognition on scanned PDF documents using PaddleOCR."""

    @staticmethod
    def extract_text_from_scanned_pdf(file_path: str) -> Dict[str, Any]:
        """
        Renders PDF pages to images and extracts text using OCR.
        """
        ocr = get_ocr_engine()
        pages: List[Dict[str, Any]] = []
        full_text_parts: List[str] = []

        try:
            doc = fitz.open(file_path)
            for page_num, page in enumerate(doc, start=1):
                # Render page to Pixmap image (300 DPI for high OCR accuracy)
                pix = page.get_pixmap(dpi=200)
                img_bytes = pix.tobytes("png")

                page_text = ""
                if ocr:
                    try:
                        import tempfile
                        with tempfile.NamedTemporaryFile(suffix=".png", delete=True) as tmp:
                            tmp.write(img_bytes)
                            tmp.flush()
                            result = ocr.ocr(tmp.name, cls=True)
                            if result and result[0]:
                                lines = [line[1][0] for line in result[0] if line and len(line) > 1]
                                page_text = "\n".join(lines)
                    except Exception as ocr_err:
                        logger.warning(f"OCR page {page_num} processing warning: {ocr_err}")

                page_text = clean_text(page_text)
                pages.append({
                    "page_number": page_num,
                    "text": page_text
                })
                if page_text:
                    full_text_parts.append(page_text)

            doc.close()
            full_text = "\n\n".join(full_text_parts)
            logger.info(f"OCR extracted {len(full_text)} characters across {len(pages)} scanned pages: {file_path}")

            return {
                "pages": pages,
                "full_text": full_text,
                "page_count": len(pages),
                "extraction_method": "ocr_paddle"
            }
        except Exception as e:
            logger.error(f"Error performing OCR on PDF {file_path}: {e}")
            raise RuntimeError(f"Failed to perform OCR on PDF: {str(e)}")
