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


outdir = Path(".scratch/reasoning-bench")
outdir.mkdir(parents=True, exist_ok=True)
images = ["img.jpg", "img1.jpg", "img2.jpg"]
efforts = ["max", "high"]
summary = []
for name in images:
    p = Path("examples") / name
    for effort in efforts:
        dest = outdir / f"{Path(name).stem}_{effort}.json"
        if dest.exists():
            print("skip existing", dest, flush=True)
            continue
        client = OpenRouterClient(
            api_key=load_key(),
            model="deepseek/deepseek-v4.1-flash",
            reasoning=effort,
            no_cache=True,
            timeout=900,
        )
        t = time.time()
        print("START", name, effort, flush=True)
        try:
            res = client.extract_bogen(
                bogen_id=f"{Path(name).stem}-{effort}",
                quelle=str(p),
                image_bytes=p.read_bytes(),
                mime_type="image/jpeg",
            )
            payload = {
                "image": name,
                "effort": effort,
                "elapsed_s": round(time.time() - t, 1),
                "usage": {
                    "prompt_tokens": res.prompt_tokens,
                    "completion_tokens": res.completion_tokens,
                    "reasoning_tokens": res.reasoning_tokens,
                    "cost_usd": res.cost_usd,
                },
                "bogen": res.bogen.model_dump(mode="json"),
            }
            dest.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
            print(
                "DONE",
                name,
                effort,
                payload["elapsed_s"],
                "s",
                payload["usage"],
                flush=True,
            )
            summary.append((name, effort, "ok", payload["elapsed_s"], payload["usage"]))
        except Exception as e:
            print("ERROR", name, effort, type(e).__name__, str(e)[:500], flush=True)
            summary.append(
                (
                    name,
                    effort,
                    f"ERROR {type(e).__name__}: {e}",
                    round(time.time() - t, 1),
                    None,
                )
            )
print("ALL DONE")
print(json.dumps(summary, ensure_ascii=False, indent=2))
