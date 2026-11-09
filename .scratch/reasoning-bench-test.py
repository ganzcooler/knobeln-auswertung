import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path("src").resolve()))
from knobeln.llm.client import OpenRouterClient


def load_key():
    for line in Path(".env").read_text().splitlines():
        if line.strip().startswith("OPENROUTER_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("no key")


img = Path("examples/img.jpg")
client = OpenRouterClient(
    api_key=load_key(),
    model="deepseek/deepseek-v4.1-flash",
    reasoning="max",
    no_cache=True,
    timeout=600,
)
t = time.time()
try:
    res = client.extract_bogen(
        bogen_id="img-test-max",
        quelle=str(img),
        image_bytes=img.read_bytes(),
        mime_type="image/jpeg",
    )
except Exception as e:
    print("ERROR", type(e).__name__, e)
    raise SystemExit(1)
print("elapsed", round(time.time() - t, 1))
print(
    "usage",
    res.prompt_tokens,
    res.completion_tokens,
    res.reasoning_tokens,
    round(res.cost_usd, 6),
)
print(
    json.dumps(res.bogen.model_dump(mode="json"), ensure_ascii=False, indent=2)[:8000]
)
