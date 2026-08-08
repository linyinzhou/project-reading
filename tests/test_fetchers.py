from __future__ import annotations

import unittest

from new_book_alert.config import Source
from new_book_alert.fetchers import _parse_douban_latest


SAMPLE_HTML = b"""
<ul>
  <li class="media clearfix">
    <div class="media__body">
      <h2 class="clearfix">
        <a class="fleft" href="https://book.douban.com/subject/12345678/">A New History</a>
      </h2>
      <p class="subject-abstract color-gray">
        [UK] Example Author / Example Translator / 2026-8-8 / Example Press / 68.00 / Hardcover
      </p>
    </div>
  </li>
</ul>
"""


class DoubanLatestParserTests(unittest.TestCase):
    def test_parses_book_metadata(self) -> None:
        source = Source("Douban History", "douban_latest", "https://book.douban.com/latest")

        books = _parse_douban_latest(SAMPLE_HTML, source)

        self.assertEqual(len(books), 1)
        self.assertEqual(books[0].title, "A New History")
        self.assertEqual(books[0].author, "[UK] Example Author / Example Translator")
        self.assertEqual(books[0].published, "2026-8-8")
        self.assertEqual(books[0].summary, "Example Press / 68.00 / Hardcover")

    def test_same_book_has_same_id_across_categories(self) -> None:
        history = Source("Douban History", "douban_latest", "https://book.douban.com/latest")
        literature = Source("Douban Literature", "douban_latest", "https://book.douban.com/latest")

        history_book = _parse_douban_latest(SAMPLE_HTML, history)[0]
        literature_book = _parse_douban_latest(SAMPLE_HTML, literature)[0]

        self.assertEqual(history_book.id, literature_book.id)


if __name__ == "__main__":
    unittest.main()
