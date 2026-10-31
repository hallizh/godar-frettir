"""Sækir greinar úr RSS-veitum."""

import calendar
import hashlib
import html
import logging
import re
import time
import urllib.parse
import urllib.request

import feedparser

log = logging.getLogger(__name__)

USER_AGENT = "GodarFrettirBot/0.1 (+https://github.com/hallizh/godar-frettir)"
TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")
IMG_RE = re.compile(r"<img[^>]+src=[\"']([^\"']+)", re.I)
OG_RE = re.compile(
    r"<meta[^>]+(?:property|name)=[\"'](?:og:image|twitter:image)(?::src)?[\"'][^>]*content=[\"']([^\"']+)"
    r"|<meta[^>]+content=[\"']([^\"']+)[\"'][^>]*(?:property|name)=[\"'](?:og:image|twitter:image)[\"']",
    re.I,
)


def article_id(link: str) -> str:
    return hashlib.sha1(link.strip().encode()).hexdigest()[:16]


def clean_text(raw: str, limit: int = 700) -> str:
    text = WS_RE.sub(" ", html.unescape(TAG_RE.sub(" ", raw or ""))).strip()
    return text[:limit]


def _image(entry) -> str | None:
    for key in ("media_content", "media_thumbnail"):
        for media in entry.get(key) or []:
            if media.get("url"):
                return media["url"]
    for enc in entry.get("enclosures") or []:
        if enc.get("type", "").startswith("image/") and enc.get("href"):
            return enc["href"]
    # Margir miðlar setja myndina inn í HTML-útdráttinn í staðinn
    for block in [entry.get("summary", "")] + [c.get("value", "") for c in entry.get("content") or []]:
        if match := IMG_RE.search(block or ""):
            return html.unescape(match.group(1))
    return None


def find_og_image(url: str, timeout: int = 15) -> str | None:
    """Sækir forsíðumynd fréttar (og:image) úr greininni sjálfri þegar veitan gefur enga mynd."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            head = resp.read(300_000).decode(resp.headers.get_content_charset() or "utf-8", "replace")
    except Exception as exc:
        log.info("Engin mynd fyrir %s: %s", url, exc)
        return None
    if match := OG_RE.search(head):
        return urllib.parse.urljoin(url, html.unescape(match.group(1) or match.group(2)))
    return None


def _published(entry) -> int:
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    return calendar.timegm(parsed) if parsed else int(time.time())


def parse_feed(raw: bytes, source: dict) -> list[dict]:
    feed = feedparser.parse(raw)
    articles = []
    for entry in feed.entries:
        link = entry.get("link")
        title = clean_text(entry.get("title", ""), 300)
        if not link or not title:
            continue
        articles.append({
            "id": article_id(link),
            "link": link,
            "title": title,
            "excerpt": clean_text(entry.get("summary", "")),
            "source": source["name"],
            "lang": source["lang"],
            "image": _image(entry),
            "published": _published(entry),
        })
    return articles


def fetch_source(source: dict, timeout: int = 20) -> list[dict]:
    req = urllib.request.Request(source["url"], headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return parse_feed(resp.read(), source)


def fetch_all(sources: list[dict]) -> list[dict]:
    """Sækir allar veitur. Veita sem bregst er skráð í log og sleppt."""
    seen, articles = set(), []
    for source in sources:
        try:
            items = fetch_source(source)
        except Exception as exc:  # ein biluð veita á ekki að stöðva keyrsluna
            log.warning("Gat ekki sótt %s (%s): %s", source["name"], source["url"], exc)
            continue
        log.info("%s: %d greinar", source["url"], len(items))
        for item in items:
            if item["id"] not in seen:
                seen.add(item["id"])
                articles.append(item)
    return articles
