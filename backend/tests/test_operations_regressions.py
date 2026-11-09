import logging
import pytest
from app.core.logging import SecretRedactionFilter
from app.core.metrics import MetricsStore


def test_redaction_preserves_nonsecret_token_messages():
    record = logging.LogRecord('test', logging.INFO, '', 0, 'Token counting completed', (), None)
    SecretRedactionFilter().filter(record)
    assert record.getMessage() == 'Token counting completed'


def test_redaction_masks_known_values_in_messages_and_extras(monkeypatch):
    import json
    from app.core.config import settings
    from app.core.logging import JsonLogFormatter
    monkeypatch.setattr(settings, 'API_KEY', 'known-test-credential')
    record = logging.LogRecord('test', logging.INFO, '', 0, 'Completed with known-test-credential', (), None)
    record.context = {'credential': 'known-test-credential'}
    SecretRedactionFilter().filter(record)
    output = json.loads(JsonLogFormatter().format(record))
    assert output['message'] == 'Completed with [REDACTED]'
    assert output['context'] == {'credential': '[REDACTED]'}


def test_json_logs_include_request_context():
    import json
    from app.core.logging import logger
    record = logging.LogRecord('bloomlens', logging.INFO, '', 0, 'request_completed', (), None)
    record.request_id, record.endpoint, record.status_code, record.duration_ms = 'req-1', '/papers/{paper_id}', 200, 12.5
    output = json.loads(logger.handlers[0].formatter.format(record))
    assert output['request_id'] == 'req-1'
    assert output['endpoint'] == '/papers/{paper_id}'
    assert output['status_code'] == 200
    assert output['duration_ms'] == 12.5


def test_metric_cardinality_is_bounded():
    store = MetricsStore()
    for index in range(1000):
        store.record_request(f'/unknown/{index}', 0.01, 404)
    assert len(store.snapshot()['endpoint_usage']) <= 101


@pytest.mark.asyncio
async def test_request_metrics_use_route_templates(client):
    from app.core.metrics import metrics
    before = metrics.snapshot()['endpoint_usage'].get('/api/v1/papers/{paper_id}', 0)
    await client.get('/api/v1/papers/887766')
    assert metrics.snapshot()['endpoint_usage'].get('/api/v1/papers/{paper_id}', 0) == before + 1


def test_mixed_pdf_runs_ocr_for_low_text_pages(tmp_path, monkeypatch):
    from app.services.document_service import DocumentService
    from app.services.pdf_service import PDFService
    from app.services.ocr_service import OCRService
    path = tmp_path / 'mixed.pdf'
    path.write_bytes(b'%PDF-test')
    monkeypatch.setattr(PDFService, 'extract_text_from_pdf', lambda path: {'pages': [{'page_number': 1, 'text': 'A readable question. ' * 20}, {'page_number': 2, 'text': ''}], 'full_text': 'A readable question. ' * 20, 'page_count': 2, 'extraction_method': 'pdf_pymupdf'})
    calls = []

    def ocr(path, page_numbers=None):
        calls.append(page_numbers)
        return {'pages': [{'page_number': 2, 'text': 'Q2. Define normalization. [5]'}], 'full_text': 'Q2. Define normalization. [5]', 'page_count': 2}

    monkeypatch.setattr(OCRService, 'extract_text_from_scanned_pdf', ocr)
    result = DocumentService.process_document(str(path))
    assert calls == [[2]]
    assert result['pages'][1]['text'] == 'Q2. Define normalization. [5]'


def test_ocr_uses_configured_dpi_and_passes_pixels_without_temp_paths(tmp_path, monkeypatch):
    import fitz
    import numpy as np
    from app.core.config import settings
    from app.services import ocr_service
    from app.services.ocr_service import OCRService
    path = tmp_path / 'scan.pdf'
    with fitz.open() as document:
        document.new_page(width=72, height=72)
        document.save(path)
    shapes = []

    class Engine:
        def ocr(self, image, cls=True):
            assert isinstance(image, np.ndarray)
            shapes.append(image.shape)
            return [[[[0, 0], ('Q1. Define keys. [5]', 0.9)]]]

    monkeypatch.setattr(settings, 'OCR_DPI', 144)
    monkeypatch.setattr(ocr_service, 'get_ocr_engine', lambda: Engine())
    result = OCRService.extract_text_from_scanned_pdf(str(path))
    assert result['full_text'] == 'Q1. Define keys. [5]'
    assert shapes == [(144, 144, 3)]
