import re
from typing import Tuple, Optional, List, Dict
from app.core.logging import logger

# Knowledge domain topic mapping dictionary (Computer Science domain focused for V1)
TOPIC_RULES: Dict[str, Dict[str, List[str]]] = {
    "Database Systems": {
        "Normalization & Normal Forms": ["normalization", "1nf", "2nf", "3nf", "bcnf", "4nf", "functional dependency"],
        "Transaction Management": ["acid", "transaction", "concurrency", "commit", "rollback", "isolation", "deadlock"],
        "Indexing & Hashing": ["b-tree", "b+ tree", "indexing", "hashing", "primary key", "foreign key"],
        "Relational Algebra & SQL": ["sql", "join", "select", "group by", "relational algebra", "query"],
    },
    "Data Structures": {
        "Trees & Binary Search Trees": ["binary tree", "bst", "avl", "red-black tree", "tree traversal", "inorder", "preorder"],
        "Graphs & Graph Algorithms": ["graph", "bfs", "dfs", "dijkstra", "shortest path", "spanning tree", "kruskal", "prim"],
        "Sorting & Searching": ["quicksort", "mergesort", "heapsort", "binary search", "hashing", "sorting"],
        "Stacks & Queues": ["stack", "queue", "push", "pop", "enqueue", "dequeue", "priority queue"],
    },
    "General Computer Science": {
        "Software Design & Architecture": ["design pattern", "architecture", "solid", "coupling", "cohesion", "uml"],
        "Operating Systems": ["process", "thread", "scheduling", "paging", "virtual memory", "deadlock", "mutex"],
        "Computer Networks": ["tcp/ip", "osi model", "ip address", "routing", "http", "socket", "dns"],
    },
}


class TopicService:
    """Service for Topic and Unit identification from question text."""

    @staticmethod
    def identify_unit(text: str) -> Optional[str]:
        """
        Identifies unit only when explicit evidence exists (e.g. 'Unit 1', 'Module 3', 'Unit-IV').
        Returns unit string or None if insufficient evidence exists. Never hallucinates units.
        """
        if not text:
            return None

        # Pattern matching explicit unit/module mentions
        match = re.search(
            r"\b(?:Unit|Module|Chapter)\s*[-:]?\s*([0-9IVXLCDM]+)\b",
            text,
            re.IGNORECASE,
        )
        if match:
            unit_val = match.group(1).upper()
            return f"Unit {unit_val}"

        return None

    @staticmethod
    def identify_topic(text: str, subject_name: Optional[str] = None) -> Tuple[Optional[str], float]:
        """
        Identifies primary topic for a question based on key technical domain concepts.
        Returns Tuple[topic_name, confidence_score]. Returns (None, 0.0) if confidence < threshold.
        """
        if not text:
            return None, 0.0

        text_lower = text.lower()

        # Check matched subject or search across all rules
        domains_to_check = []
        if subject_name and subject_name in TOPIC_RULES:
            domains_to_check.append(TOPIC_RULES[subject_name])
        for domain in TOPIC_RULES.values():
            if domain not in domains_to_check:
                domains_to_check.append(domain)

        best_topic = None
        best_score = 0.0

        for domain in domains_to_check:
            for topic, keywords in domain.items():
                matches = sum(1 for kw in keywords if kw in text_lower)
                if matches > 0:
                    score = min(1.0, 0.5 + (matches * 0.2))
                    if score > best_score:
                        best_score = score
                        best_topic = topic

        if best_score >= 0.5:
            return best_topic, best_score

        return None, 0.0

    @staticmethod
    def classify_question_type(text: str) -> Tuple[str, float]:
        """
        Classifies question into standard categories:
        Definition, Short Answer, Descriptive, Numerical, Problem Solving, Comparison, Case Study, Design, Programming, Other
        """
        if not text:
            return "Other", 0.5

        t_lower = text.lower()

        if any(w in t_lower for w in ["write a program", "code", "implement in python", "c++ program", "java code"]):
            return "Programming", 0.90
        elif any(w in t_lower for w in ["calculate", "compute", "find the value", "evaluate the numerical"]):
            return "Numerical", 0.85
        elif any(w in t_lower for w in ["compare", "differentiate", "distinguish between", "difference between"]):
            return "Comparison", 0.90
        elif any(w in t_lower for w in ["design", "architect", "draw an erd", "schema for"]):
            return "Design", 0.85
        elif any(w in t_lower for w in ["define", "what is", "state", "list"]):
            return "Definition", 0.85
        elif any(w in t_lower for w in ["explain", "describe", "discuss", "elaborate"]):
            return "Descriptive", 0.80
        elif any(w in t_lower for w in ["case study", "scenario", "suppose a system"]):
            return "Case Study", 0.85
        elif any(w in t_lower for w in ["solve", "apply", "construct"]):
            return "Problem Solving", 0.80

        return "Descriptive", 0.60
