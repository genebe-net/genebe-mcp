"""Helpers keeping tool responses small."""


def truncate_text(text: str, limit: int) -> tuple[str, bool]:
    """Cut ``text`` to ``limit`` characters on a line boundary when possible."""
    if len(text) <= limit:
        return text, False
    cut = text[:limit]
    newline = cut.rfind("\n")
    if newline > limit // 2:
        cut = cut[:newline]
    return cut.rstrip() + "\n[... truncated ...]", True


def take[T](items: list[T], limit: int) -> tuple[list[T], bool]:
    """Return at most ``limit`` items and whether anything was dropped."""
    return items[:limit], len(items) > limit
