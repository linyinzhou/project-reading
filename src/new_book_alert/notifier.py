from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request


class NotificationError(RuntimeError):
    pass


def send_serverchan(title: str, markdown: str) -> None:
    sendkey = os.environ.get("SERVERCHAN_SENDKEY", "").strip()
    if not sendkey:
        raise NotificationError("SERVERCHAN_SENDKEY is not set.")

    url = f"https://sctapi.ftqq.com/{sendkey}.send"
    payload = urllib.parse.urlencode({"title": title, "desp": markdown}).encode("utf-8")
    request = urllib.request.Request(url, data=payload, method="POST")

    with urllib.request.urlopen(request, timeout=20) as response:
        body = response.read().decode("utf-8", errors="replace")

    try:
        data = json.loads(body)
    except json.JSONDecodeError as exc:
        raise NotificationError(f"Unexpected ServerChan response: {body}") from exc

    if data.get("code") != 0:
        raise NotificationError(f"ServerChan returned an error: {body}")
