# Góðar fréttir

Íslensk fréttasíða sem birtir eingöngu góðar, vonarríkar og uppörvandi fréttir.

Á klukkutíma fresti keyrir GitHub Action sem:

1. sækir nýjar greinar úr RSS-veitum íslenskra og erlendra miðla (`godar/sources.py`),
2. lætur Claude meta hverja grein: er þetta góð frétt (einkunn 0–10), í hvaða flokk fer hún, og stutt samantekt á íslensku (`godar/classify.py`),
3. vistar birtar greinar í `data/` (greinar sem var hafnað eru líka skráðar svo þær séu ekki metnar aftur),
4. byggir kyrrstæða vefsíðu (`templates/`, `static/`) og birtir hana á GitHub Pages.

## Uppsetning

1. **Settings → Secrets and variables → Actions**: bættu við `ANTHROPIC_API_KEY`.
2. **Settings → Pages**: veldu *Source: GitHub Actions*.
3. Keyrðu *Uppfæra fréttir* handvirkt undir **Actions**, eða bíddu eftir næstu heilu klukkustund.

## Keyra á eigin vél

```sh
pip install -r requirements.txt
python -m godar demo        # prufusíða með sýnigögnum, engin API-köll
export ANTHROPIC_API_KEY=...
python -m godar run         # raunveruleg keyrsla
open site/index.html
python -m pytest            # prófanir
```

## Stillingar

| Breyta | Sjálfgefið | Lýsing |
|---|---|---|
| `GODAR_MODEL` | `claude-opus-5-5` | Claude-líkanið sem metur fréttirnar |
| `GODAR_MIN_SCORE` | `7` | Lágmarkseinkunn til að frétt birtist |
| `--limit` | `150` | Hámark nýrra greina sem eru metnar í hverri keyrslu |

Flokkar eru skilgreindir í `godar/categories.py` og fréttaveitur í `godar/sources.py`.
