# 03 — LLM-Client, Prompt, JSON-Schema, Cache

Status: resolved
Blocked by: 01, 02

## Ziel

Ein austauschbarer OpenRouter-Client, der einen Bogen als Bild liest und strukturiertes JSON zurückgibt. Standardmodell ist ausschließlich `deepseek/deepseek-v4.1-flash` mit maximalem Reasoning.

## Aufgaben

- `llm/client.py`: OpenAI-kompatibler Client mit `base_url=https://openrouter.ai/api/v1`, Modell aus Config, `temperature=0`, `reasoning={"effort": "max", "exclude": true}`, hohes `max_tokens`.
- `llm/prompt.py`: deutscher Prompt mit Layout, vollständiger Wertungsliste, `/`/leer-Regeln, Normalisierungsregeln und dem Verbot, die Summenzeile als Korrekturquelle zu nutzen.
- `llm/schema.py`: JSON-Schema/Pydantic-Modelle für `bogen_unklar`, `durchgang_nr`, vier Spieler, zwölf Wurf-Zeilen und die Summenzeile.
- `llm/cache.py`: Cache unter `.cache/knobeln/`, Schlüssel = `Bogen_ID` + Modell + Prompt-Version + Reasoning-Effort; `--no-cache` umgeht ihn.
- Retries mit Backoff bei 429/5xx/Timeout; ein Reparatur-Retry bei ungültigem JSON, danach technischer Fehler.
- Tokenverbrauch und geschätzte Kosten loggen; API-Key nie loggen.
- Fake-Client für Tests, der Fixture-JSON zurückgibt.

## Abnahmekriterien

- Ein Fake-Client kann die Pipeline ohne Netzwerk betreiben.
- Das Schema verlangt vier Spieler und zwölf Wurf-Zeilen; fehlende Werte sind `null`. Leere Spieler-/Wurf-Listen werden clientseitig als fehlende Werte gepaddet und markiert.
- Ungültiges JSON führt zu genau einem Reparatur-Retry und danach zu einem technischen Fehler.
- Cache-Treffer vermeiden einen zweiten API-Aufruf.
- Kein anderes Modell als Default; kein stiller Fallback.

## Referenzen

- `../spec.md` §6
- `../issues/09-real-model-smoke-test.md`
