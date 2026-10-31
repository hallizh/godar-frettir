"""RSS-veitur sem eru skannaðar. Bættu við eða fjarlægðu að vild.

`lang` segir líkaninu á hvaða máli fréttin er; allar samantektir eru skrifaðar á íslensku.
"""

SOURCES = [
    # Íslenskir miðlar
    {"name": "RÚV", "url": "https://www.ruv.is/rss/frettir", "lang": "is"},
    {"name": "mbl.is", "url": "https://www.mbl.is/feeds/innlent/", "lang": "is"},
    {"name": "mbl.is", "url": "https://www.mbl.is/feeds/erlent/", "lang": "is"},
    {"name": "mbl.is", "url": "https://www.mbl.is/feeds/taekni/", "lang": "is"},
    {"name": "Vísir", "url": "https://www.visir.is/rss/allt", "lang": "is"},
    {"name": "DV", "url": "https://www.dv.is/feed/", "lang": "is"},
    # Erlendir miðlar sem sérhæfa sig í góðum fréttum
    {"name": "Good News Network", "url": "https://www.goodnewsnetwork.org/feed/", "lang": "en"},
    {"name": "Positive News", "url": "https://www.positive.news/feed/", "lang": "en"},
    {"name": "Reasons to be Cheerful", "url": "https://reasonstobecheerful.world/feed/", "lang": "en"},
    {"name": "The Guardian", "url": "https://www.theguardian.com/world/series/the-upside/rss", "lang": "en"},
    # Almennir erlendir miðlar, síaðir
    {"name": "BBC", "url": "https://feeds.bbci.co.uk/news/world/rss.xml", "lang": "en"},
    {"name": "BBC", "url": "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml", "lang": "en"},
    {"name": "BBC", "url": "https://feeds.bbci.co.uk/news/health/rss.xml", "lang": "en"},
    {"name": "BBC", "url": "https://feeds.bbci.co.uk/news/technology/rss.xml", "lang": "en"},
    {"name": "ScienceDaily", "url": "https://www.sciencedaily.com/rss/top.xml", "lang": "en"},
]
