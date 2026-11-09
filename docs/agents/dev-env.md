# Development Environment

- `uv` liegt oft unter `~/.local/bin/uv`: `export PATH="$HOME/.local/bin:$PATH"`.
- Setup: `uv sync --group dev`, dann `uv run pre-commit install`.
- `.env` mit `OPENROUTER_API_KEY`; Key-Check ohne Ausgabe:
  `uv run python -c "from dotenv import load_dotenv; import os; load_dotenv('.env'); print('key present' if os.getenv('OPENROUTER_API_KEY') else 'missing')"`
- Git-Remote ist SSH: `git@github.com:ganzcooler/knobeln-auswertung.git`. `gh auth login` braucht nur, wer `gh pr create` nutzen will; der PR-Link funktioniert auch manuell.
- Scratch-Verzeichnis: `mktemp -d` oder `/tmp/$USER`; `/tmp/opencode` kann einem anderen User gehören.
- Checks: `./scripts/check.sh`; Umgebungscheck: `./scripts/doctor.sh`; echter Smoke-Test: `uv run pytest --run-manual`.
