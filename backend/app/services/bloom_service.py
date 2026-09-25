import concurrent.futures
import json
import re
import threading
from typing import Dict, Any, List, Tuple, Optional
import numpy as np

from app.core.config import settings
from app.core.logging import logger
from app.schemas.bloom import BloomClassificationResult, GeminiBloomResponse
from app.services.embedding_service import EmbeddingService


BLOOM_LEVEL_MAP = {
    "L1": 1,
    "L2": 2,
    "L3": 3,
    "L4": 4,
    "L5": 5,
    "L6": 6,
}

BLOOM_NAME_MAP = {
    "L1": "Remember",
    "L2": "Understand",
    "L3": "Apply",
    "L4": "Analyze",
    "L5": "Evaluate",
    "L6": "Create",
}

# Reference sentences for semantic Bloom anchor vectors
BLOOM_ANCHOR_EXAMPLES = {
    "L1": [
        "Define normalization.",
        "List the basic components of a database system.",
        "State Newton's third law of motion.",
        "Recall the definition of a binary search tree."
    ],
    "L2": [
        "Explain the process of normalization and functional dependency.",
        "Describe how concurrency control works in database transactions.",
        "Summarize the key differences between process and thread.",
        "Interpret the given ER diagram and discuss entity sets."
    ],
    "L3": [
        "Apply 3NF to normalize the given database relation.",
        "Calculate the shortest path between nodes using Dijkstra algorithm.",
        "Demonstrate the execution of quicksort on the given array.",
        "Solve the given differential equation using Laplace transform."
    ],
    "L4": [
        "Compare 2NF and 3NF normalization forms.",
        "Analyze the time and space complexity of merge sort versus heap sort.",
        "Differentiate between TCP and UDP transport layer protocols.",
        "Distinguish between optimistic and pessimistic concurrency control."
    ],
    "L5": [
        "Evaluate normalization performance for this high-throughput transactional database.",
        "Justify the choice of NoSQL database over relational SQL database for social media feeds.",
        "Critique the proposed system architecture and assess its security risks.",
        "Defend the choice of microservices architecture over monolithic design."
    ],
    "L6": [
        "Design a normalized database schema for an e-commerce platform.",
        "Develop an algorithm to detect cycles in a directed graph.",
        "Construct a compiler front-end parser using LL(1) grammar rules.",
        "Formulate a novel routing protocol for ad-hoc sensor networks."
    ]
}

# Pre-computed anchor vectors cache
_anchor_vectors_cache: Optional[Dict[str, np.ndarray]] = None
_anchor_vectors_lock = threading.Lock()


def _get_anchor_vectors() -> Dict[str, np.ndarray]:
    """Generates average anchor embedding vector per Bloom level (L1-L6) with double-checked lock."""
    global _anchor_vectors_cache
    if _anchor_vectors_cache is not None:
        return _anchor_vectors_cache

    with _anchor_vectors_lock:
        if _anchor_vectors_cache is not None:
            return _anchor_vectors_cache

        cache = {}
        for level, examples in BLOOM_ANCHOR_EXAMPLES.items():
            vecs = EmbeddingService.get_embeddings_batch(examples)
            valid_vecs = [v for v in vecs if v is not None]
            if valid_vecs:
                avg_vec = np.mean(valid_vecs, axis=0)
                # Normalize vector
                norm = np.linalg.norm(avg_vec)
                if norm > 0:
                    avg_vec = avg_vec / norm
                cache[level] = avg_vec
        _anchor_vectors_cache = cache
        return cache


class BloomService:
    """
    Production Hybrid Bloom Taxonomy Classifier.
    Combines Verb Analysis, Cognitive Operation Hierarchy, Semantic Vector Analysis,
    Question Structure Analysis, Weighted Scoring, and Gemini Verification fallback.
    """

    VERB_DICTIONARY = {
        "L1": ["define", "list", "identify", "state", "name", "recall", "repeat", "label", "match", "select", "what is"],
        "L2": ["explain", "describe", "summarize", "discuss", "interpret", "classify", "outline", "paraphrase", "illustrate", "express"],
        "L3": ["apply", "demonstrate", "calculate", "solve", "execute", "implement", "compute", "use", "show", "perform"],
        "L4": ["analyze", "compare", "differentiate", "contrast", "distinguish", "examine", "deconstruct", "investigate", "break down"],
        "L5": ["evaluate", "justify", "critique", "assess", "judge", "defend", "recommend", "rate", "appraise", "benchmark"],
        "L6": ["design", "develop", "construct", "formulate", "architect", "propose", "build", "invent", "devise", "synthesize", "create"],
    }

    @classmethod
    def classify_question(cls, text: str) -> BloomClassificationResult:
        """
        Main classifier entry point. Performs hybrid scoring, confidence calculation,
        and triggers Gemini verification fallback when confidence < threshold.
        """
        if not text or not text.strip():
            return cls._default_result("L1")

        # 1. Component Signal Analyses
        verb_scores, detected_verbs = cls._analyze_verbs(text)
        semantic_scores = cls._analyze_semantic(text)
        cognitive_scores, cognitive_op = cls._analyze_cognitive_operation(text, detected_verbs)
        structure_scores = cls._analyze_question_structure(text)

        # 2. Weighted Aggregation across L1 - L6
        w_verb = settings.BLOOM_WEIGHT_VERB
        w_sem = settings.BLOOM_WEIGHT_SEMANTIC
        w_cog = settings.BLOOM_WEIGHT_COGNITIVE
        w_struct = settings.BLOOM_WEIGHT_STRUCTURE

        final_scores: Dict[str, float] = {}
        for lvl in ["L1", "L2", "L3", "L4", "L5", "L6"]:
            score = (
                w_verb * verb_scores.get(lvl, 0.0)
                + w_sem * semantic_scores.get(lvl, 0.0)
                + w_cog * cognitive_scores.get(lvl, 0.0)
                + w_struct * structure_scores.get(lvl, 0.0)
            )
            final_scores[lvl] = float(score)

        # Determine primary level (highest cognitive level when compound operations present)
        best_level = max(final_scores, key=lambda k: final_scores[k])
        max_score = final_scores[best_level]
        total_score_sum = sum(final_scores.values()) or 1.0

        # Confidence calculation
        confidence = float(min(0.98, max(0.40, max_score / total_score_sum * 1.5)))

        result = BloomClassificationResult(
            primary_level=best_level,
            bloom_level_id=BLOOM_LEVEL_MAP[best_level],
            confidence=confidence,
            explanation=f"Hybrid classification based on detected verbs ({', '.join(detected_verbs) if detected_verbs else 'None'}) and cognitive operation '{cognitive_op}'.",
            detected_verbs=detected_verbs,
            cognitive_operation=cognitive_op,
            component_scores={
                "verb_score": float(verb_scores.get(best_level, 0.0)),
                "semantic_score": float(semantic_scores.get(best_level, 0.0)),
                "cognitive_score": float(cognitive_scores.get(best_level, 0.0)),
                "structure_score": float(structure_scores.get(best_level, 0.0)),
            },
            candidate_scores=final_scores,
            classifier_source="hybrid",
            gemini_verification_status="not_required" if confidence >= settings.BLOOM_VERIFICATION_THRESHOLD else "pending",
        )

        # 3. Low Confidence -> Gemini Verification Fallback
        if confidence < settings.BLOOM_VERIFICATION_THRESHOLD and settings.GEMINI_API_KEY:
            gemini_res = cls._verify_with_gemini(text, result)
            if gemini_res:
                return gemini_res

            result.gemini_verification_status = "failed_or_skipped"

        return result

    @classmethod
    def _analyze_verbs(cls, text: str) -> Tuple[Dict[str, float], List[str]]:
        text_lower = text.lower()
        verb_scores = {lvl: 0.0 for lvl in BLOOM_LEVEL_MAP}
        detected = []

        for lvl, verbs in cls.VERB_DICTIONARY.items():
            for v in verbs:
                # Match verb as word boundary or start of sentence
                pattern = r"\b" + re.escape(v) + r"\b"
                if re.search(pattern, text_lower):
                    detected.append(v)
                    verb_scores[lvl] += 1.0

        # Normalize verb scores
        total = sum(verb_scores.values())
        if total > 0:
            verb_scores = {k: v / total for k, v in verb_scores.items()}

        return verb_scores, detected

    @classmethod
    def _analyze_semantic(cls, text: str) -> Dict[str, float]:
        scores = {lvl: 0.0 for lvl in BLOOM_LEVEL_MAP}
        q_vec = EmbeddingService.get_embedding(text)

        if q_vec is None:
            return scores

        anchors = _get_anchor_vectors()
        for lvl, a_vec in anchors.items():
            sim = float(np.dot(q_vec, a_vec))
            scores[lvl] = max(0.0, sim)

        # Normalize semantic scores
        max_s = max(scores.values()) or 1.0
        if max_s > 0:
            scores = {k: v / max_s for k, v in scores.items()}

        return scores

    @classmethod
    def _analyze_cognitive_operation(cls, text: str, detected_verbs: List[str]) -> Tuple[Dict[str, float], str]:
        """
        Analyzes cognitive operation hierarchy:
        Recall -> Understand -> Apply -> Analyze -> Evaluate -> Create
        For compound questions, returns highest cognitive level.
        """
        scores = {lvl: 0.0 for lvl in BLOOM_LEVEL_MAP}
        t_lower = text.lower()

        detected_levels = []
        for lvl, verbs in cls.VERB_DICTIONARY.items():
            if any(v in detected_verbs for v in verbs):
                detected_levels.append(lvl)

        if not detected_levels:
            return scores, "General Comprehension"

        # Determine highest cognitive level among detected (L6 > L5 > L4 > L3 > L2 > L1)
        highest = max(detected_levels, key=lambda l: BLOOM_LEVEL_MAP[l])
        scores[highest] = 1.0

        if len(detected_levels) > 1:
            cog_op = f"Compound cognitive task spanning {', '.join(detected_levels)}; primary level {highest}"
        else:
            cog_op = f"Single operation targeting {BLOOM_NAME_MAP[highest]}"

        return scores, cog_op

    @classmethod
    def _analyze_question_structure(cls, text: str) -> Dict[str, float]:
        """Analyzes question length, problem complexity, and architectural creation cues."""
        scores = {lvl: 0.0 for lvl in BLOOM_LEVEL_MAP}
        t_lower = text.lower()

        # Check L6 Create vs L5 Evaluate vs L4 Analyze
        if any(w in t_lower for w in ["design", "architect", "propose a new", "construct", "formulate"]):
            scores["L6"] = 0.90
        elif any(w in t_lower for w in ["evaluate", "justify", "critique", "assess"]):
            scores["L5"] = 0.85
        elif any(w in t_lower for w in ["compare", "contrast", "differentiate", "distinguish"]):
            scores["L4"] = 0.85
        elif any(w in t_lower for w in ["apply", "calculate", "solve", "compute"]):
            scores["L3"] = 0.80
        elif any(w in t_lower for w in ["explain", "describe", "discuss"]):
            scores["L2"] = 0.75
        else:
            scores["L1"] = 0.70

        return scores

    @classmethod
    def _verify_with_gemini(cls, text: str, initial_result: BloomClassificationResult) -> Optional[BloomClassificationResult]:
        """
        Calls Google Gemini SDK (`google-genai`) for low-confidence fallback verification.
        Validates response via Pydantic `GeminiBloomResponse`.
        """
        if not settings.GEMINI_API_KEY:
            return None

        prompt = f"""
Act as an expert computer science professor evaluating examination questions using Revised Bloom's Taxonomy.

Taxonomy Levels:
L1 - Remember (Recall facts/definitions)
L2 - Understand (Explain concepts)
L3 - Apply (Calculate, solve, execute)
L4 - Analyze (Compare, differentiate, examine)
L5 - Evaluate (Justify decisions, critique, assess)
L6 - Create (Design, construct, architect new solutions)

Analyze this question:
"{text}"

Initial Hybrid AI suggestion: {initial_result.primary_level} ({BLOOM_NAME_MAP[initial_result.primary_level]})

Return ONLY a JSON object matching this structure:
{{
  "bloom_level": "L1/L2/L3/L4/L5/L6",
  "bloom_name": "Remember/Understand/Apply/Analyze/Evaluate/Create",
  "confidence": 0.95,
  "cognitive_operation": "Brief description of cognitive operation",
  "detected_verbs": ["verb1"],
  "reason": "Detailed justification"
}}
"""
        try:
            from google import genai
            client = genai.Client(api_key=settings.GEMINI_API_KEY)

            # Enforce 10-second timeout on synchronous Gemini API call to prevent worker thread exhaustion
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(
                    client.models.generate_content,
                    model="gemini-2.5-flash",
                    contents=prompt,
                )
                response = future.result(timeout=10.0)

            if response and response.text:
                json_str = response.text.strip()
                # Clean markdown json code blocks if present
                if json_str.startswith("```"):
                    json_str = re.sub(r"^```[a-z]*\n|\n```$", "", json_str, flags=re.IGNORECASE)

                data = json.loads(json_str)
                validated = GeminiBloomResponse(**data)

                level_code = validated.bloom_level
                return BloomClassificationResult(
                    primary_level=level_code,
                    bloom_level_id=BLOOM_LEVEL_MAP[level_code],
                    confidence=validated.confidence,
                    explanation=f"Gemini Verified: {validated.reason}",
                    detected_verbs=validated.detected_verbs,
                    cognitive_operation=validated.cognitive_operation,
                    component_scores=initial_result.component_scores,
                    candidate_scores=initial_result.candidate_scores,
                    classifier_source="gemini_verified",
                    gemini_verification_status="verified",
                )

        except Exception as e:
            logger.warning(f"Gemini verification fallback failed gracefully: {e}")

        return None

    @classmethod
    def _default_result(cls, level_code: str = "L1") -> BloomClassificationResult:
        return BloomClassificationResult(
            primary_level=level_code,
            bloom_level_id=BLOOM_LEVEL_MAP[level_code],
            confidence=0.50,
            explanation="Default classification due to empty text.",
            detected_verbs=[],
            cognitive_operation="None",
            component_scores={},
            candidate_scores={},
            classifier_source="hybrid",
            gemini_verification_status="not_required",
        )
