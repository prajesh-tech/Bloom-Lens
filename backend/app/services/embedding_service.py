import threading
from typing import List, Optional
import numpy as np
from app.core.config import settings
from app.core.logging import logger

_embedding_model = None
_fallback_vectorizer = None
_model_lock = threading.Lock()
_vectorizer_lock = threading.Lock()


def get_fallback_vectorizer():
    """Fallback n-gram HashingVectorizer when SentenceTransformers model is offline/unavailable."""
    global _fallback_vectorizer
    if _fallback_vectorizer is not None:
        return _fallback_vectorizer
    with _vectorizer_lock:
        if _fallback_vectorizer is None:
            from sklearn.feature_extraction.text import HashingVectorizer
            _fallback_vectorizer = HashingVectorizer(n_features=384, alternate_sign=False, norm="l2")
    return _fallback_vectorizer


def get_embedding_model():
    """Lazily loads SentenceTransformer model to preserve boot performance with double-checked lock."""
    global _embedding_model
    if _embedding_model is not None:
        return _embedding_model if _embedding_model is not False else None
    with _model_lock:
        if _embedding_model is None:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info(f"Loading SentenceTransformer model: {settings.EMBEDDING_MODEL_NAME}...")
                _embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
                logger.info("SentenceTransformer model loaded successfully.")
            except Exception as e:
                logger.warning(f"Failed to load SentenceTransformer model ({settings.EMBEDDING_MODEL_NAME}): {e}")
                _embedding_model = False
    return _embedding_model if _embedding_model is not False else None


def get_embedding_backend_status() -> str:
    if _embedding_model is False:
        return "fallback"
    if _embedding_model is not None:
        return "model_loaded"
    return "not_loaded"


class EmbeddingService:
    """Service for generating normalized sentence vector embeddings."""

    @classmethod
    def get_embedding(cls, text: str) -> Optional[np.ndarray]:
        """Generates a 1D float32 normalized vector for text."""
        if not text or not text.strip():
            return None

        model = get_embedding_model()
        if model:
            try:
                vec = model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
                return vec.astype(np.float32)
            except Exception as e:
                logger.error(f"Error generating model embedding: {e}")

        # Robust scikit-learn TF-IDF / HashingVectorizer fallback
        try:
            vec_sparse = get_fallback_vectorizer().transform([text])
            vec = vec_sparse.toarray()[0].astype(np.float32)
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            return vec
        except Exception as fallback_err:
            logger.error(f"Error generating fallback vector: {fallback_err}")
            return None

    @classmethod
    def get_embeddings_batch(cls, texts: List[str]) -> List[Optional[np.ndarray]]:
        """Generates normalized vector embeddings for a list of texts."""
        if not texts:
            return []

        model = get_embedding_model()
        if model:
            try:
                vecs = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
                return [v.astype(np.float32) for v in vecs]
            except Exception as e:
                logger.error(f"Error generating batch model embeddings: {e}")

        # Fallback batch generation
        res = []
        for t in texts:
            res.append(cls.get_embedding(t))
        return res
