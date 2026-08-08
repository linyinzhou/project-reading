from __future__ import annotations

import hashlib
import json
import os
import re
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from html import unescape
from typing import Any

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
    body = _download(source.url, timeout)
    if source.type.lower() in {"rss", "atom", "xml"}:
        return _parse_feed(body, source)
    if source.type.lower() == "json":
        return _parse_json(body, source)
    raise ValueError(f"Unsupported source type: {source.type}")


def _download(url: str, timeout: int) -> bytes:
    url = _apply_rsshub_base(url)
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "project-reading/0.1 (+https://github.com/linyinzhou/project-reading)"
        },
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
    title = _clean_text(str(get_nested(item, fields.get("title", "title")) or ""))
    link = _clean_text(str(get_nested(item, fields.get("link", "link")) or ""))
    author = _clean_text(str(get_nested(item, fields.get("author", "author")) or ""))
    published = _clean_text(str(get_nested(item, fields.get("published", "published")) or ""))
    summary = _clean_text(str(get_nested(item, fields.get("summary", "summary")) or ""))

    return BookItem(
        id=_stable_id(title, link, source.name),
        title=title,
        link=link,
        source=source.name,
        author=author,
        published=published,
        summary=summary,
    )


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


def _stable_id(title: str, link: str, source_name: str) -> str:
    raw = "|".join([source_name, link, title]).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]
