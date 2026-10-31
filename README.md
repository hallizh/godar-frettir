# Góðar fréttir

Íslensk fréttasíða sem birtir eingöngu góðar, vonarríkar og uppörvandi fréttir.

Á 15 mínútna fresti keyrir GitHub Action sem:

1. sækir nýjar greinar úr RSS-veitum íslenskra og erlendra miðla (`godar/sources.py`),
2. lætur gervigreind (Codex eða Claude) meta hverja grein: er þetta góð frétt (einkunn 0–10), í hvaða flokk fer hún, og stutt samantekt á íslensku (`godar/classify.py`),
3. vistar birtar greinar í `data/` (greinar sem var hafnað eru líka skráðar svo þær séu ekki metnar aftur),
4. byggir kyrrstæða vefsíðu (`templates/`, `static/`) og birtir hana á GitHub Pages.

## Uppsetning

Sjálfgefið er notuð Codex-innskráning (ChatGPT-áskrift), svo enginn API-lykill þarf.

1. Skráðu þig inn í Codex á eigin vél: `npm i -g @openai/codex && codex login`.
2. **Settings → Secrets and variables → Actions → Secrets**:
   - `CODEX_AUTH_JSON`: allt innihald `~/.codex/auth.json`.
   - `GH_SECRETS_TOKEN`: fine-grained token fyrir þetta repo með heimildina *Secrets: Read and write*.
     Codex endurnýjar innskráninguna reglulega og gamla útgáfan hættir þá að virka, svo keyrslan
     vistar nýju útgáfuna aftur í `CODEX_AUTH_JSON` með þessum token.
3. **Settings → Pages**: veldu *Source: GitHub Actions*.
4. Keyrðu *Uppfæra fréttir* handvirkt undir **Actions**, eða bíddu í mesta lagi 15 mínútur.

Ef innskráningin rennur samt út: keyrðu `codex login` aftur og settu nýja `auth.json` í `CODEX_AUTH_JSON`.

**Claude í staðinn:** settu breytuna `GODAR_PROVIDER=claude` undir *Variables* og leyndarmálið `ANTHROPIC_API_KEY`.

## Keyra á eigin vél

```sh
pip install -r requirements.txt
python -m godar demo        # prufusíða með sýnigögnum, engin API-köll
python -m godar run         # raunveruleg keyrsla (notar codex login á vélinni)
open site/index.html
python -m pytest            # prófanir
```

## Stillingar

| Breyta | Sjálfgefið | Lýsing |
|---|---|---|
| `GODAR_PROVIDER` | `codex` | `codex` (ChatGPT-innskráning) eða `claude` (Anthropic API-lykill) |
| `GODAR_MODEL` | sjálfgefið líkan Codex / `claude-opus-5-5` | Líkanið sem metur fréttirnar |
| `GODAR_MIN_SCORE` | `7` | Lágmarkseinkunn til að frétt birtist |
| `--limit` | `500` | Hámark nýrra greina sem eru metnar í hverri keyrslu |

Flokkar eru skilgreindir í `godar/categories.py` og fréttaveitur í `godar/sources.py`.
