def escape_like(value: str) -> str:
    """Escape literal SQL LIKE input; callers add their own surrounding wildcards."""
    return value.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
