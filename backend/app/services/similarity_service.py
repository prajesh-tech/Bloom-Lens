import threading
from typing import List, Dict, Any, Tuple
import numpy as np
from app.core.config import settings
from app.core.logging import logger
from app.utils.text_cleaner import normalize_question_text

_faiss_available = None
_faiss_lock = threading.Lock()


def check_faiss():
    global _faiss_available
    if _faiss_available is None:
        with _faiss_lock:
            if _faiss_available is None:
                try:
                    import faiss
                    _faiss_available = True
                except ImportError:
                    _faiss_available = False
                    logger.warning('FAISS unavailable; using numpy vector search')
    return _faiss_available


class SimilarityIndex:
    """One immutable subject/backend-compatible corpus index per upload."""
    def __init__(self, corpus_data, backend=None):
        self.questions = [question for question, _ in corpus_data]
        self.corpus = [(q, vector) for q, vector in corpus_data
                       if vector is not None and (backend is None or q.get('embedding_backend') == backend)]
        self.index = None
        self.vectors = None
        if self.corpus:
            self.vectors = np.vstack([vector for _, vector in self.corpus]).astype(np.float32)
            if check_faiss():
                import faiss
                self.index = faiss.IndexFlatIP(self.vectors.shape[1])
                self.index.add(self.vectors)

    def search(self, text, vector, top_k=5):
        if not text or not self.questions:
            return []
        normalized = normalize_question_text(text)
        matches = {}
        for question in self.questions:
            candidate = question.get('normalized_text') or normalize_question_text(question.get('original_text', ''))
            if normalized and normalized == candidate:
                matches[question['id']] = self._match(question, 1.0, 'exact_repeat')
        if vector is not None and self.vectors is not None:
            if self.index is not None:
                scores, indexes = self.index.search(np.asarray([vector], dtype=np.float32), min(top_k, len(self.corpus)))
                candidates = [(float(score), self.corpus[index][0]) for score, index in zip(scores[0], indexes[0]) if index >= 0]
            else:
                scores = np.dot(self.vectors, vector)
                candidates = sorted([(float(score), self.corpus[index][0]) for index, score in enumerate(scores)], reverse=True, key=lambda item: item[0])[:top_k]
            for score, question in candidates:
                if question['id'] in matches:
                    continue
                if score >= settings.SIMILARITY_THRESHOLD_EXACT:
                    classification = 'near_duplicate'
                elif score >= settings.SIMILARITY_THRESHOLD_SEMANTIC:
                    classification = 'potentially_repeated'
                else:
                    continue
                matches[question['id']] = self._match(question, score, classification)
        return sorted(matches.values(), key=lambda item: item['similarity_score'], reverse=True)[:top_k]

    @staticmethod
    def _match(question, score, classification):
        return {'question_id': question['id'], 'question_number': question.get('question_number', ''),
                'original_text': question.get('original_text', ''), 'similarity_score': round(min(1.0, score), 4),
                'similarity_type': 'exact_repeat' if classification == 'exact_repeat' else 'semantic_repeat',
                'classification': classification}


class SimilarityService:
    @classmethod
    def build_index(cls, corpus_data, backend=None):
        return SimilarityIndex(corpus_data, backend)

    @classmethod
    def find_similar_questions_prebuilt(cls, target_text: str, target_vec: np.ndarray,
        corpus_data: List[Tuple[Dict[str, Any], np.ndarray]], top_k: int = 5, backend=None) -> List[Dict[str, Any]]:
        return cls.build_index(corpus_data, backend).search(target_text, target_vec, top_k)
