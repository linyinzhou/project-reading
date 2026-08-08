from __future__ import annotations

import hashlib
import json
import os
import re
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from html import unescape
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urljoin

from .config import Source, get_nested


@dataclass(frozen=True)
class BookItem:
    id: str
    title: str
    link: str
    source: str
    author: str = ""
    published: str = ""
    summary: str = ""


def fetch_source(source: Source, timeout: int) -> list[BookItem]:
    body = _download(source.url, timeout, source.type)
    if source.type.lower() in {"rss", "atom", "xml"}:
        return _parse_feed(body, source)
    if source.type.lower() == "json":
        return _parse_json(body, source)
    if source.type.lower() == "douban_latest":
        return _parse_douban_latest(body, source)
    raise ValueError(f"Unsupported source type: {source.type}")


def _download(url: str, timeout: int, source_type: str = "") -> bytes:
    url = _apply_rsshub_base(url)
    headers = {
        "User-Agent": "project-reading/0.1 (+https://github.com/linyinzhou/project-reading)"
    }
    if source_type.lower() == "douban_latest":
        headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 Chrome/127.0 Safari/537.36"
                ),
                "Referer": "https://book.douban.com/",
            }
        )
    request = urllib.request.Request(
        url,
        headers=headers,
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def _apply_rsshub_base(url: str) -> str:
    base_url = os.environ.get("RSSHUB_BASE_URL", "").strip().rstrip("/")
    default_base = "https://rsshub.app"
    if base_url and url.startswith(default_base):
        return base_url + url[len(default_base) :]
    return url


def _parse_feed(body: bytes, source: Source) -> list[BookItem]:
    root = ET.fromstring(body)
    channel_items = root.findall(".//item")
    atom_items = root.findall(".//{http://www.w3.org/2005/Atom}entry")
    raw_items = channel_items or atom_items

    return [_feed_item_to_book(item, source) for item in raw_items]


def _feed_item_to_book(item: ET.Element, source: Source) -> BookItem:
    title = _clean_text(_find_text(item, ["title", "{http://www.w3.org/2005/Atom}title"]))
    link = _clean_text(_find_link(item))
    summary = _clean_text(
        _find_text(
            item,
            [
                "description",
                "summary",
                "{http://www.w3.org/2005/Atom}summary",
                "{http://purl.org/rss/1.0/modules/content/}encoded",
            ],
        )
    )
    published = _clean_text(
        _find_text(item, ["pubDate", "published", "updated", "{http://www.w3.org/2005/Atom}updated"])
    )

    return BookItem(
        id=_stable_id(title, link, source.name),
        title=title,
        link=link,
        source=source.name,
        published=published,
        summary=summary,
    )


def _parse_json(body: bytes, source: Source) -> list[BookItem]:
    data = json.loads(body.decode("utf-8"))
    items = get_nested(data, source.items_path)
    if isinstance(items, dict):
        items = list(items.values())
    if not isinstance(items, list):
        return []

    fields = source.fields or {}
    return [_json_item_to_book(item, source, fields) for item in items if isinstance(item, dict)]


def _json_item_to_book(item: dict[str, Any], source: Source, fields: dict[str, str]) -> BookItem:
    title = _clean_value(get_nested(item, fields.get("title", "title")))
    link = _clean_value(get_nested(item, fields.get("link", "link")))
    author = _clean_value(get_nested(item, fields.get("author", "author")))
    published = _clean_value(get_nested(item, fields.get("published", "published")))
    summary = _clean_value(get_nested(item, fields.get("summary", "summary")))

    return BookItem(
        id=_stable_id(title, link, source.name),
        title=title,
        link=link,
        source=source.name,
        author=author,
        published=published,
        summary=summary,
    )


class _DoubanLatestParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.items: list[dict[str, str]] = []
        self.current: dict[str, str] | None = None
        self.in_heading = False
        self.in_title_link = False
        self.in_abstract = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        classes = set((attributes.get("class") or "").split())

        if tag == "li" and {"media", "clearfix"}.issubset(classes):
            self.current = {"title": "", "link": "", "abstract": ""}
        elif self.current is not None and tag == "h2":
            self.in_heading = True
        elif self.current is not None and tag == "a" and self.in_heading:
            href = attributes.get("href") or ""
            if "/subject/" in href:
                self.current["link"] = href
                self.in_title_link = True
        elif self.current is not None and tag == "p" and "subject-abstract" in classes:
            self.in_abstract = True

    def handle_data(self, data: str) -> None:
        if self.current is None:
            return
        if self.in_title_link:
            self.current["title"] += data
        elif self.in_abstract:
            self.current["abstract"] += data

    def handle_endtag(self, tag: str) -> None:
        if tag == "a":
            self.in_title_link = False
        elif tag == "h2":
            self.in_heading = False
        elif tag == "p":
            self.in_abstract = False
        elif tag == "li" and self.current is not None:
            if self.current["title"] and self.current["link"]:
                self.items.append(self.current)
            self.current = None


def _parse_douban_latest(body: bytes, source: Source) -> list[BookItem]:
    parser = _DoubanLatestParser()
    parser.feed(body.decode("utf-8"))

    books: list[BookItem] = []
    for item in parser.items:
        title = _clean_text(item["title"])
        link = urljoin(source.url, _clean_text(item["link"]))
        author, published, summary = _parse_douban_abstract(item["abstract"])
        books.append(
            BookItem(
                id=_stable_id(title, link, source.name),
                title=title,
                link=link,
                source=source.name,
                author=author,
                published=published,
                summary=summary,
            )
        )
    return books


def _parse_douban_abstract(value: str) -> tuple[str, str, str]:
    parts = [_clean_text(part) for part in value.split("/") if _clean_text(part)]
    date_index = next(
        (index for index, part in enumerate(parts) if re.fullmatch(r"\d{4}(?:-\d{1,2}){0,2}", part)),
        None,
    )
    if date_index is None:
        return " / ".join(parts), "", ""

    author = " / ".join(parts[:date_index])
    published = parts[date_index]
    summary = " / ".join(parts[date_index + 1 :])
    return author, published, summary


def _find_text(item: ET.Element, names: list[str]) -> str:
    for name in names:
        child = item.find(name)
        if child is not None and child.text:
            return child.text
    return ""


def _find_link(item: ET.Element) -> str:
    text_link = _find_text(item, ["link"])
    if text_link:
        return text_link

    atom_link = item.find("{http://www.w3.org/2005/Atom}link")
    if atom_link is not None:
        return atom_link.attrib.get("href", "")
    return ""


def _clean_text(value: str) -> str:
    value = unescape(value or "")
    value = re.sub(r"<[^>]+>", "", value)
    return re.sub(r"\s+", " ", value).strip()


def _clean_value(value: Any) -> str:
    if isinstance(value, list):
        return _clean_text(" / ".join(str(item) for item in value if item is not None))
    return _clean_text(str(value or ""))


def _stable_id(title: str, link: str, source_name: str) -> str:
    del source_name
    raw = "|".join([link, title]).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]
