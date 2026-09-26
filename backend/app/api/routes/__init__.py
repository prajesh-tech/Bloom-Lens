"""API route handlers."""

from app.api.routes import health, papers, questions, analytics, courses, course_outcomes

__all__ = ["health", "papers", "questions", "analytics", "courses", "course_outcomes"]
