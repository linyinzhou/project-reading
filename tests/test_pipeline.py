from __future__ import annotations

import unittest

from new_book_alert.fetchers import BookItem
from new_book_alert.pipeline import _select_balanced_books


class BalancedSelectionTests(unittest.TestCase):
    def test_round_robins_across_sources(self) -> None:
        books = [
            BookItem(id="a1", title="A1", link="", source="A"),
            BookItem(id="a2", title="A2", link="", source="A"),
            BookItem(id="a3", title="A3", link="", source="A"),
            BookItem(id="b1", title="B1", link="", source="B"),
            BookItem(id="b2", title="B2", link="", source="B"),
        ]

        selected = _select_balanced_books(books, 4)

        self.assertEqual([book.id for book in selected], ["a1", "b1", "a2", "b2"])


if __name__ == "__main__":
    unittest.main()
