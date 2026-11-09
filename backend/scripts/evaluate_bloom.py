"""Deterministic internal classifier evaluation, without Google or model downloads.

Run from backend: .venv/bin/python -m scripts.evaluate_bloom
"""
import csv
import json
from pathlib import Path
from unittest.mock import patch
from app.services.bloom_service import BloomService

DATA = Path(__file__).parents[1] / 'tests' / 'data' / 'bloom_evaluation.csv'


def evaluate():
    matrix = {f'L{i}': {f'L{j}': 0 for j in range(1, 7)} for i in range(1, 7)}
    with DATA.open() as source:
        rows = list(csv.DictReader(source))
    # Fix the embedding backend, anchors, and external verification for reproducibility.
    with patch('app.services.embedding_service._embedding_model', False), patch('app.services.bloom_service._anchor_vectors_cache', None), patch('app.core.config.settings.GEMINI_API_KEY', ''):
        for row in rows:
            predicted = BloomService.classify_question(row['question']).primary_level
            matrix[row['label']][predicted] += 1
    correct = sum(matrix[level][level] for level in matrix)
    return {'questions': len(rows), 'subjects': sorted({row['subject'] for row in rows}),
            'accuracy': correct / len(rows), 'confusion_matrix': matrix,
            'mode': 'internal authored templates; hashing embeddings; Gemini disabled'}


if __name__ == '__main__':
    print(json.dumps(evaluate(), indent=2))
