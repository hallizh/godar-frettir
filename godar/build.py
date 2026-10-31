"""Býr til kyrrstæða vefsíðu úr birtum fréttum."""

import shutil
import time
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .categories import CATEGORIES

ROOT = Path(__file__).resolve().parent.parent
MONTHS = ["janúar", "febrúar", "mars", "apríl", "maí", "júní", "júlí",
          "ágúst", "september", "október", "nóvember", "desember"]
PER_PAGE = 60
WEEKDAYS = ["mánudagur", "þriðjudagur", "miðvikudagur", "fimmtudagur", "föstudagur", "laugardagur", "sunnudagur"]
TOP_COUNT = 13  # forsíðufrétt + 4 í hliðardálki + 8 í „Nýjast“
SECTION_COUNT = 4


def time_ago(ts: int, now: float) -> str:
    minutes = max(0, int((now - ts) // 60))
    if minutes < 60:
        return "rétt í þessu" if minutes < 5 else f"fyrir {minutes} mín."
    hours = minutes // 60
    if hours < 24:
        return f"fyrir {hours} klst."
    days = hours // 24
    if days == 1:
        return "í gær"
    if days < 7:
        return f"fyrir {days} dögum"
    d = datetime.fromtimestamp(ts, timezone.utc)
    return f"{d.day}. {MONTHS[d.month - 1]}"


def home_sections(articles: list[dict]) -> list[tuple[str, list[dict]]]:
    """Fréttir hvers flokks fyrir neðan toppinn á forsíðunni, án endurtekninga."""
    shown = {a["id"] for a in articles[:TOP_COUNT]}
    sections = []
    for key in CATEGORIES:
        items = [a for a in articles if a["category"] == key and a["id"] not in shown][:SECTION_COUNT]
        if len(items) >= 2:  # stakt spjald í heilli röð lítur illa út
            sections.append((key, items))
    return sections


def build(articles: list[dict], out: Path, demo: bool = False, now: float | None = None) -> None:
    now = now or time.time()
    env = Environment(loader=FileSystemLoader(ROOT / "templates"), autoescape=select_autoescape())
    env.filters["ago"] = lambda ts: time_ago(ts, now)
    stamp = datetime.fromtimestamp(now, timezone.utc)
    common = {
        "categories": CATEGORIES,
        "demo": demo,
        "updated": f"{stamp.day}. {MONTHS[stamp.month - 1]} kl. {stamp:%H:%M}",
        "today": f"{WEEKDAYS[stamp.weekday()].capitalize()} {stamp.day}. {MONTHS[stamp.month - 1]}",
    }

    if out.exists():
        shutil.rmtree(out)
    (out / "flokkur").mkdir(parents=True)
    shutil.copytree(ROOT / "static", out / "static")
    if demo:
        shutil.copytree(ROOT / "demo" / "img", out / "demo-img")

    (out / "index.html").write_text(env.get_template("home.html").render(
        **common, active=None, base="", articles=articles, sections=home_sections(articles)))
    page = env.get_template("category.html")
    for key, label in CATEGORIES.items():
        items = [a for a in articles if a["category"] == key][:PER_PAGE]
        (out / "flokkur" / f"{key}.html").write_text(page.render(
            **common, active=key, heading=label, base="../", articles=items))
    (out / "um.html").write_text(env.get_template("about.html").render(**common, active="um", base=""))
