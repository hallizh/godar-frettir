import time
from types import SimpleNamespace

from godar import classify
from godar.build import build, time_ago
from godar.fetch import parse_feed
from godar.store import Store

RSS = """<?xml version="1.0"?><rss version="2.0"><channel><title>T</title>
<item><title>Ný meðferð</title><link>https://a.is/1</link><description>&lt;p&gt;Góð &amp;amp; fín&lt;/p&gt;</description>
<pubDate>Fri, 30 Oct 2026 10:00:00 GMT</pubDate></item>
<item><title>Engin slóð</title></item>
</channel></rss>""".encode()


def test_parse_feed_cleans_and_skips():
    items = parse_feed(RSS, {"name": "RÚV", "lang": "is"})
    assert len(items) == 1
    assert items[0]["excerpt"] == "Góð & fín"
    assert items[0]["source"] == "RÚV"


class FakeMessages:
    def parse(self, **kwargs):
        verdicts = classify.BatchVerdicts(verdicts=[
            classify.Verdict(id="a", score=9, good_news=True, category="laekningar",
                             title_is="Gott", summary_is="Mjög gott.", reason="r"),
            classify.Verdict(id="b", score=2, good_news=False, category="erlent",
                             title_is="Slæmt", summary_is="Slæmt.", reason="r"),
            classify.Verdict(id="ókunnugt", score=9, good_news=True, category="erlent",
                             title_is="x", summary_is="x", reason="r"),
        ])
        return SimpleNamespace(stop_reason="end_turn", parsed_output=verdicts)


def test_classify_filters_unknown_ids_and_threshold():
    arts = [{"id": i, "source": "s", "lang": "is", "title": "t", "excerpt": "e"} for i in ("a", "b")]
    result = classify.classify(arts, client=SimpleNamespace(messages=FakeMessages()))
    assert set(result) == {"a", "b"}
    assert classify.is_published(result["a"]) and not classify.is_published(result["b"])


def test_store_roundtrip_and_prune(tmp_path):
    s = Store(tmp_path)
    now = time.time()
    s.add({"id": "new", "published": now})
    s.add({"id": "old", "published": now - 40 * 86400})
    s.mark_seen("new")
    s.prune(now)
    s.save()
    s2 = Store(tmp_path)
    assert list(s2.articles) == ["new"] and not s2.is_new({"id": "new"})


def test_build_writes_pages(tmp_path):
    art = {"id": "a", "link": "https://a.is", "title_is": "<b>Gott</b>", "summary_is": "s", "source": "RÚV",
           "lang": "is", "image": None, "published": int(time.time()), "category": "taekni", "score": 9}
    build([art], tmp_path / "site")
    html = (tmp_path / "site" / "flokkur" / "taekni.html").read_text()
    assert "&lt;b&gt;Gott" in html  # autoescape
    assert (tmp_path / "site" / "index.html").exists()


def test_time_ago():
    assert time_ago(1000, 1000 + 3 * 3600) == "fyrir 3 klst."


def test_image_from_summary_html_and_og_regex():
    rss = """<?xml version="1.0"?><rss version="2.0"><channel><item><title>T</title><link>https://a.is/2</link>
<description>&lt;img src="https://a.is/mynd.jpg"&gt; texti</description></item></channel></rss>""".encode()
    assert parse_feed(rss, {"name": "x", "lang": "is"})[0]["image"] == "https://a.is/mynd.jpg"
    from godar.fetch import OG_RE
    m = OG_RE.search('<meta content="/m.jpg" property="og:image">')
    assert (m.group(1) or m.group(2)) == "/m.jpg"
