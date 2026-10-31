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


def build(articles: list[dict], out: Path, demo: bool = False, now: float | None = None) -> None:
    now = now or time.time()
    env = Environment(loader=FileSystemLoader(ROOT / "templates"), autoescape=select_autoescape())
    env.filters["ago"] = lambda ts: time_ago(ts, now)
    stamp = datetime.fromtimestamp(now, timezone.utc)
    common = {
        "categories": CATEGORIES,
        "demo": demo,
        "updated": f"{stamp.day}. {MONTHS[stamp.month - 1]} kl. {stamp:%H:%M}",
    }

    if out.exists():
        shutil.rmtree(out)
    (out / "flokkur").mkdir(parents=True)
    shutil.copytree(ROOT / "static", out / "static")

    page = env.get_template("list.html")
    (out / "index.html").write_text(page.render(
        **common, active=None, heading="Nýjustu góðu fréttirnar", base="", articles=articles[:PER_PAGE]))
    for key, label in CATEGORIES.items():
        items = [a for a in articles if a["category"] == key][:PER_PAGE]
        (out / "flokkur" / f"{key}.html").write_text(page.render(
            **common, active=key, heading=label, base="../", articles=items))
    (out / "um.html").write_text(env.get_template("about.html").render(**common, active="um", base=""))
