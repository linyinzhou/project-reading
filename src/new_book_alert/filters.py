from __future__ import annotations

from .fetchers import BookItem


def filter_books(
    books: list[BookItem],
    include_keywords: list[str],
    exclude_keywords: list[str],
) -> list[BookItem]:
    filtered: list[BookItem] = []
    seen_ids: set[str] = set()

    for book in books:
        searchable = _searchable_text(book)
        if book.id in seen_ids:
            continue
        if _contains_any(searchable, exclude_keywords):
            continue
        if include_keywords and not _contains_any(searchable, include_keywords):
            continue
        filtered.append(book)
        seen_ids.add(book.id)

    return filtered


def _searchable_text(book: BookItem) -> str:
    return " ".join([book.title, book.author, book.summary, book.source]).lower()


def _contains_any(text: str, keywords: list[str]) -> bool:
    normalized = text.lower()
    return any(keyword.lower() in normalized for keyword in keywords if keyword)
