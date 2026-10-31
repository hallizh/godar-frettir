"""Lætur Claude meta hvort frétt sé góð frétt, flokka hana og skrifa íslenska samantekt."""

import json
import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Literal

import anthropic
from pydantic import BaseModel, Field

from .categories import CATEGORIES

log = logging.getLogger(__name__)

# "codex" notar innskráningu Codex CLI (ChatGPT-áskrift), "claude" notar ANTHROPIC_API_KEY
PROVIDER = os.environ.get("GODAR_PROVIDER", "codex")
MODEL = os.environ.get("GODAR_MODEL", "claude-opus-5-5" if PROVIDER == "claude" else "")
CODEX_BIN = os.environ.get("GODAR_CODEX_BIN", "codex")
BATCH_SIZE = 15
MIN_SCORE = int(os.environ.get("GODAR_MIN_SCORE", "7"))

CategoryKey = Literal[tuple(CATEGORIES)]  # type: ignore[valid-type]


class Verdict(BaseModel):
    id: str
    score: int = Field(description="0 = mjög neikvæð frétt, 10 = einstaklega uppörvandi frétt")
    good_news: bool = Field(description="Á þessi frétt heima á síðu með góðum fréttum?")
    category: CategoryKey
    title_is: str = Field(description="Stutt, lýsandi fyrirsögn á íslensku")
    summary_is: str = Field(description="2-3 setningar á íslensku um hvað gerðist og af hverju það er gott")
    reason: str = Field(description="Ein stutt setning um matið (fyrir ritstjórn, ekki birt)")


class BatchVerdicts(BaseModel):
    verdicts: list[Verdict]


SYSTEM = f"""Þú ert ritstjóri íslensku fréttasíðunnar „Góðar fréttir“, sem birtir eingöngu jákvæðar, vonarríkar og uppörvandi fréttir.

Þú færð lista af fréttum (á íslensku eða ensku) með fyrirsögn og útdrætti. Fyrir hverja frétt:

1. Gefðu einkunn 0-10 fyrir hversu uppörvandi hún er. Góð frétt segir frá raunverulegum framförum, árangri, uppgötvun, hjálpsemi, björgun, bata, nýsköpun, náttúruvernd eða einhverju sem gleður fólk.
2. Settu good_news=true aðeins ef fréttin er í raun góð frétt í heild sinni. Hafnaðu:
   - fréttum þar sem harmleikur, ofbeldi, dauðsföll, stríð eða slys eru meginefnið, jafnvel þótt einhver ljós punktur sé í þeim;
   - stjórnmáladeilum, kjaradeilum, dómsmálum og hneykslismálum;
   - auglýsingum, kynningarefni, slúðri um frægt fólk og smelluefni;
   - úrslitum íþróttaleikja nema um sé að ræða sérstakt afrek eða fallega sögu.
3. Veldu einn flokk: {", ".join(f"{k} ({v})" for k, v in CATEGORIES.items())}.
   Veldu sértækasta efnisflokkinn sem á við (t.d. taekni, laekningar, visindi, umhverfi, dyralif, ithrottir, menning). Notaðu innlent fyrir almennar íslenskar fréttir og erlent fyrir almennar erlendar fréttir.
4. Skrifaðu fyrirsögn og 2-3 setninga samantekt á vandaðri, eðlilegri íslensku. Haltu þig við staðreyndirnar í útdrættinum og bættu engu við sem þar kemur ekki fram. Ekki nota upphrópanir eða ofhlaðið orðalag.

Skilaðu einni niðurstöðu fyrir hverja frétt, með sama id og fréttin hafði."""


def _batch_prompt(articles: list[dict]) -> str:
    payload = [
        {"id": a["id"], "source": a["source"], "lang": a["lang"], "title": a["title"], "excerpt": a["excerpt"]}
        for a in articles
    ]
    return "Metið þessar fréttir:\n\n" + json.dumps(payload, ensure_ascii=False, indent=1)


# JSON Schema fyrir svar Codex. OpenAI krefst þess að allir reitir séu skyldugir og engir aukareitir leyfðir.
CODEX_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["verdicts"],
    "properties": {"verdicts": {"type": "array", "items": {
        "type": "object",
        "additionalProperties": False,
        "required": list(Verdict.model_fields),
        "properties": {
            "id": {"type": "string"},
            "score": {"type": "integer"},
            "good_news": {"type": "boolean"},
            "category": {"type": "string", "enum": list(CATEGORIES)},
            "title_is": {"type": "string"},
            "summary_is": {"type": "string"},
            "reason": {"type": "string"},
        },
    }}},
}


def _keep_known(verdicts: list[Verdict], articles: list[dict]) -> list[Verdict]:
    ids = {a["id"] for a in articles}
    return [v for v in verdicts if v.id in ids]


def classify_batch_codex(articles: list[dict], timeout: int = 600) -> list[Verdict]:
    """Keyrir `codex exec` án verkfæra og les svarið samkvæmt CODEX_SCHEMA."""
    with tempfile.TemporaryDirectory() as tmp:
        schema, out = Path(tmp) / "schema.json", Path(tmp) / "out.json"
        schema.write_text(json.dumps(CODEX_SCHEMA))
        cmd = [CODEX_BIN, "exec", "--ephemeral", "--skip-git-repo-check", "--sandbox", "read-only",
               "--cd", tmp, "--output-schema", str(schema), "--output-last-message", str(out), "-"]
        if MODEL:
            cmd[2:2] = ["--model", MODEL]
        prompt = SYSTEM + "\n\nSvaraðu eingöngu með JSON samkvæmt skemanu. Ekki keyra neinar skipanir.\n\n" + _batch_prompt(articles)
        proc = subprocess.run(cmd, input=prompt, capture_output=True, text=True, timeout=timeout)
        if proc.returncode != 0 or not out.exists():
            raise RuntimeError(f"codex exec mistókst ({proc.returncode}): {proc.stderr[-2000:]}")
        return _keep_known(BatchVerdicts.model_validate_json(out.read_text()).verdicts, articles)


def classify_batch(client: anthropic.Anthropic, articles: list[dict]) -> list[Verdict]:
    response = client.messages.parse(
        model=MODEL,
        max_tokens=16000,
        system=SYSTEM,
        output_config={"effort": "low"},
        messages=[{"role": "user", "content": _batch_prompt(articles)}],
        output_format=BatchVerdicts,
    )
    if response.stop_reason == "refusal" or response.parsed_output is None:
        log.warning("Engin niðurstaða fyrir lotu (stop_reason=%s)", response.stop_reason)
        return []
    return _keep_known(response.parsed_output.verdicts, articles)


def classify(articles: list[dict], client: anthropic.Anthropic | None = None,
             provider: str = PROVIDER) -> dict[str, Verdict]:
    """Skilar mati fyrir hverja grein sem tókst að meta, eftir id."""
    if provider == "claude":
        client = client or anthropic.Anthropic()
    results: dict[str, Verdict] = {}
    for start in range(0, len(articles), BATCH_SIZE):
        batch = articles[start:start + BATCH_SIZE]
        try:
            verdicts = classify_batch(client, batch) if provider == "claude" else classify_batch_codex(batch)
        except (anthropic.APIError, RuntimeError, subprocess.TimeoutExpired, ValueError) as exc:
            log.error("Villa við mat á lotu %d: %s", start // BATCH_SIZE, exc)
            continue
        for verdict in verdicts:
            results[verdict.id] = verdict
    return results


def is_published(verdict: Verdict) -> bool:
    return verdict.good_news and verdict.score >= MIN_SCORE
