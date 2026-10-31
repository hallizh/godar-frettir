"""Keyrsla: python -m godar run | python -m godar demo"""

import argparse
import json
import logging
import time
from pathlib import Path

from .build import ROOT, build
from .store import Store

log = logging.getLogger("godar")


def run(out: Path, limit: int) -> None:
    from .classify import MODEL, PROVIDER, classify, is_published
    from .fetch import fetch_all, find_og_image
    from .sources import SOURCES

    store = Store()
    fresh = [a for a in fetch_all(SOURCES) if store.is_new(a)]
    # Nýjustu fyrst, og takmark á hverja keyrslu svo kostnaður haldist fyrirsjáanlegur
    fresh.sort(key=lambda a: a["published"], reverse=True)
    fresh = fresh[:limit]
    log.info("%d nýjar greinar til mats með %s %s", len(fresh), PROVIDER, MODEL or "(sjálfgefið líkan)")

    verdicts = classify(fresh) if fresh else {}
    published = 0
    for article in fresh:
        verdict = verdicts.get(article["id"])
        if verdict is None:
            continue  # metum aftur í næstu keyrslu
        store.mark_seen(article["id"])
        if is_published(verdict):
            if not article["image"]:
                article["image"] = find_og_image(article["link"])
            store.add({**article, **verdict.model_dump(exclude={"id", "reason", "good_news"})})
            published += 1
    log.info("%d af %d metnum greinum birtar", published, len(verdicts))

    store.prune()
    store.save()
    build(store.latest(), out)


def demo(out: Path) -> None:
    now = int(time.time())
    articles = json.loads((ROOT / "demo" / "sample.json").read_text())
    for i, a in enumerate(articles):
        a["published"] = now - a.pop("age_minutes", i * 90) * 60
    build(articles, out, demo=True, now=now)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(prog="godar")
    parser.add_argument("command", choices=["run", "demo"])
    parser.add_argument("--out", type=Path, default=ROOT / "site")
    parser.add_argument("--limit", type=int, default=500, help="hámarksfjöldi nýrra greina sem eru metnar í hverri keyrslu")
    args = parser.parse_args()
    if args.command == "run":
        run(args.out, args.limit)
    else:
        demo(args.out)
    log.info("Vefur skrifaður í %s", args.out)


if __name__ == "__main__":
    main()
