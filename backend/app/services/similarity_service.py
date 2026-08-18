from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from app.core.config import settings
from app.core.logging import logger
from app.services.embedding_service import EmbeddingService
from app.utils.text_cleaner import normalize_question_text

_faiss_available = None


def check_faiss():
    """Checks FAISS CPU availability."""
    global _faiss_available
    if _faiss_available is None:
        try:
            import faiss
            _faiss_available = True
        except ImportError:
            _faiss_available = False
            logger.warning("faiss-cpu package not installed. Vector search fallback will use numpy dot product.")
    return _faiss_available


class SimilarityService:
    """
    Question Similarity Engine using FAISS CPU vector search and exact text normalization.
    Detects exact duplicate questions and semantically repeated questions across historical papers.
    """

    @classmethod
    def find_similar_questions_prebuilt(
        cls,
        target_text: str,
        target_vec: np.ndarray,
        corpus_data: List[Tuple[Dict[str, Any], np.ndarray]],
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Compares target_text/target_vec against a pre-computed corpus of questions and vectors.
        """
        if not target_text or not corpus_data:
            return []

        norm_target = normalize_question_text(target_text)
        matches: List[Dict[str, Any]] = []

        # 1. First Pass: Check Exact Repeats (Normalized String Match)
        for q, _ in corpus_data:
            corpus_text = q.get("normalized_text") or normalize_question_text(q.get("original_text", ""))
            if norm_target == corpus_text and norm_target:
                matches.append({
                    "question_id": q["id"],
                    "question_number": q.get("question_number", ""),
                    "original_text": q.get("original_text", ""),
                    "similarity_score": 1.0,
                    "similarity_type": "exact_repeat",
                    "classification": "exact_repeat",
                })

        # 2. Second Pass: Vector Similarity Search
        valid_corpus = [item for item in corpus_data if not any(m["question_id"] == item[0]["id"] for m in matches)]
        
        if valid_corpus:
            vectors = np.vstack([item[1] for item in valid_corpus]).astype(np.float32)
            scores = []
            
            if check_faiss():
                import faiss
                index = faiss.IndexFlatIP(vectors.shape[1])
                index.add(vectors)
                D, I = index.search(np.expand_dims(target_vec, axis=0).astype(np.float32), min(top_k, len(valid_corpus)))
                for sim_score, idx in zip(D[0], I[0]):
                    if idx >= 0:
                        scores.append((float(sim_score), valid_corpus[idx][0]))
            else:
                sims = np.dot(vectors, target_vec)
                for idx, sim in enumerate(sims):
                    scores.append((float(sim), valid_corpus[idx][0]))

            scores.sort(key=lambda x: x[0], reverse=True)
            for score, q in scores[:top_k]:
                if score >= settings.SIMILARITY_THRESHOLD_EXACT:
                    classification, sim_type = "exact_repeat", "exact_repeat"
                elif score >= settings.SIMILARITY_THRESHOLD_SEMANTIC:
                    classification, sim_type = "potentially_repeated", "semantic_repeat"
                else:
                    continue
                matches.append({
                    "question_id": q["id"],
                    "question_number": q.get("question_number", ""),
                    "original_text": q.get("original_text", ""),
                    "similarity_score": round(score, 4),
                    "similarity_type": sim_type,
                    "classification": classification,
                })
        return matches

    @classmethod
    def find_similar_questions(
        cls,
        target_text: str,
        corpus_questions: List[Dict[str, Any]],
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Compares target_text against a corpus of existing questions.
        Returns list of similar question matches with similarity score and classification.
        """
        if not target_text or not corpus_questions:
            return []

        norm_target = normalize_question_text(target_text)
        target_vec = EmbeddingService.get_embedding(target_text)

        matches: List[Dict[str, Any]] = []

        # 1. First Pass: Check Exact Repeats (Normalized String Match)
        for q in corpus_questions:
            corpus_text = q.get("normalized_text") or normalize_question_text(q.get("original_text", ""))

            if norm_target == corpus_text and norm_target:
                matches.append({
                    "question_id": q["id"],
                    "question_number": q.get("question_number", ""),
                    "original_text": q.get("original_text", ""),
                    "similarity_score": 1.0,
                    "similarity_type": "exact_repeat",
                    "classification": "exact_repeat",
                })
                continue

        # 2. Second Pass: Vector Similarity Search using FAISS CPU or NumPy
        if target_vec is not None and corpus_questions:
            # Build vector corpus for non-exact matches
            valid_corpus = []
            vectors = []

            for q in corpus_questions:
                # Skip if already added as exact match
                if any(m["question_id"] == q["id"] for m in matches):
                    continue

                q_text = q.get("original_text", "")
                vec = EmbeddingService.get_embedding(q_text)
                if vec is not None:
                    valid_corpus.append(q)
                    vectors.append(vec)

            if vectors and len(vectors) > 0:
                vec_matrix = np.vstack(vectors).astype(np.float32)

                # Use FAISS CPU or Numpy dot product
                scores = []
                if check_faiss():
                    import faiss
                    dim = vec_matrix.shape[1]
                    index = faiss.IndexFlatIP(dim)
                    index.add(vec_matrix)

                    query_matrix = np.expand_dims(target_vec, axis=0).astype(np.float32)
                    top_k_val = min(top_k, len(valid_corpus))
                    D, I = index.search(query_matrix, top_k_val)

                    for sim_score, idx in zip(D[0], I[0]):
                        if idx >= 0 and idx < len(valid_corpus):
                            scores.append((float(sim_score), valid_corpus[idx]))
                else:
                    # Numpy fallback cosine similarity
                    sims = np.dot(vec_matrix, target_vec)
                    for idx, sim in enumerate(sims):
                        scores.append((float(sim), valid_corpus[idx]))

                # Process top similarity candidates
                scores.sort(key=lambda x: x[0], reverse=True)
                for score, q in scores[:top_k]:
                    if score >= settings.SIMILARITY_THRESHOLD_EXACT:
                        classification = "exact_repeat"
                        sim_type = "exact_repeat"
                    elif score >= settings.SIMILARITY_THRESHOLD_SEMANTIC:
                        classification = "potentially_repeated"
                        sim_type = "semantic_repeat"
                    else:
                        classification = "different"
                        sim_type = "semantic_repeat"

                    if classification != "different":
                        matches.append({
                            "question_id": q["id"],
                            "question_number": q.get("question_number", ""),
                            "original_text": q.get("original_text", ""),
                            "similarity_score": round(score, 4),
                            "similarity_type": sim_type,
                            "classification": classification,
                        })

        return matches
