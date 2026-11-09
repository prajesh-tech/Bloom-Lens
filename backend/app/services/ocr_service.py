import threading
import numpy as np
from importlib.metadata import version
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
                    if int(version("paddleocr").split(".")[0]) >= 3:
                        _ocr_engine = PaddleOCR(lang=settings.OCR_LANG, use_doc_orientation_classify=False,
                            use_doc_unwarping=False, use_textline_orientation=True)
                    else:
                        _ocr_engine = PaddleOCR(use_angle_cls=True, lang=settings.OCR_LANG, show_log=False)
                logger.info("PaddleOCR engine initialized successfully.")
            except Exception as e:
                logger.warning(f"PaddleOCR engine failed to initialize: {e}")
                _ocr_engine = False
    return _ocr_engine if _ocr_engine is not False else None


class OCRService:
    """Service for optical character recognition on scanned PDF documents using PaddleOCR."""

    @staticmethod
    def extract_text_from_scanned_pdf(file_path: str, page_numbers: List[int] | None = None) -> Dict[str, Any]:
        ocr = get_ocr_engine()
        pages = []
        try:
            with fitz.open(file_path) as document:
                page_count = document.page_count
                for page_number, page in enumerate(document, start=1):
                    if page_numbers is not None and page_number not in page_numbers:
                        continue
                    text = ""
                    if ocr:
                        try:
                            pix = page.get_pixmap(dpi=settings.OCR_DPI, colorspace=fitz.csRGB, alpha=False)
                            rgb = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)
                            image = rgb[:, :, ::-1].copy()
                            if hasattr(ocr, "predict"):
                                predictions = ocr.predict(image)
                                lines = [line for prediction in predictions for line in prediction.get("rec_texts", []) if isinstance(line, str)]
                            else:
                                result = ocr.ocr(image, cls=True)
                                lines = [line[1][0] for line in (result[0] if result and result[0] else [])
                                         if line and len(line) > 1 and isinstance(line[1][0], str)]
                            text = clean_text("\n".join(lines))
                        except Exception:
                            logger.warning("OCR page processing failed", extra={"page_number": page_number})
                    pages.append({"page_number": page_number, "text": text})
            return {"pages": pages, "full_text": "\n\n".join(page["text"] for page in pages if page["text"]),
                    "page_count": page_count, "extraction_method": "ocr_paddle"}
        except Exception as error:
            logger.error("PDF OCR failed")
            raise RuntimeError("Failed to perform OCR on PDF") from error
