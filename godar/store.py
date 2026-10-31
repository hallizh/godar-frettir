"""Geymir birtar fréttir og þær sem hafa þegar verið metnar, í JSON-skrám í data/."""

import json
import time
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
KEEP_DAYS = 30


class Store:
    def __init__(self, data_dir: Path = DATA_DIR):
        self.dir = data_dir
        self.articles: dict[str, dict] = self._load("articles.json")
        # Allar greinar sem hafa verið metnar, líka þær sem var hafnað, svo við borgum ekki tvisvar
        self.seen: dict[str, int] = self._load("seen.json")

    def _load(self, name: str) -> dict:
        path = self.dir / name
        return json.loads(path.read_text()) if path.exists() else {}

    def is_new(self, article: dict) -> bool:
        return article["id"] not in self.seen

    def mark_seen(self, article_id: str) -> None:
        self.seen[article_id] = int(time.time())

    def add(self, article: dict) -> None:
        self.articles[article["id"]] = article

    def prune(self, now: float | None = None) -> None:
        cutoff = (now or time.time()) - KEEP_DAYS * 86400
        self.articles = {k: a for k, a in self.articles.items() if a["published"] >= cutoff}
        # seen geymist aðeins lengur svo gamlar greinar sem dúkka aftur upp verði ekki metnar á ný
        self.seen = {k: t for k, t in self.seen.items() if t >= cutoff - KEEP_DAYS * 86400}

    def latest(self) -> list[dict]:
        return sorted(self.articles.values(), key=lambda a: a["published"], reverse=True)

    def save(self) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        for name, data in (("articles.json", self.articles), ("seen.json", self.seen)):
            (self.dir / name).write_text(json.dumps(data, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
