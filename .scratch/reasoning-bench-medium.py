import json, sys, time
from pathlib import Path
sys.path.insert(0, str(Path('src').resolve()))
from knobeln.llm.client import OpenRouterClient

def load_key():
    for line in Path('.env').read_text().splitlines():
        if line.strip().startswith('OPENROUTER_API_KEY='):
            return line.split('=',1)[1].strip().strip('"').strip("'")
    raise SystemExit('no key')

outdir = Path('.scratch/reasoning-bench'); outdir.mkdir(parents=True, exist_ok=True)
for name in ['img.jpg','img1.jpg','img2.jpg']:
    p = Path('examples')/name
    dest = outdir/f'{Path(name).stem}_medium.json'
    if dest.exists():
        print('skip existing', dest, flush=True); continue
    client = OpenRouterClient(api_key=load_key(), model='deepseek/deepseek-v4.1-flash', reasoning='medium', no_cache=True, timeout=900)
    t=time.time(); print('START', name, 'medium', flush=True)
    try:
        res = client.extract_bogen(bogen_id=f'{Path(name).stem}-medium', quelle=str(p), image_bytes=p.read_bytes(), mime_type='image/jpeg')
        payload={'image':name,'effort':'medium','elapsed_s':round(time.time()-t,1),'usage':{'prompt_tokens':res.prompt_tokens,'completion_tokens':res.completion_tokens,'reasoning_tokens':res.reasoning_tokens,'cost_usd':res.cost_usd},'bogen':res.bogen.model_dump(mode='json')}
        dest.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
        print('DONE', name, payload['elapsed_s'], 's', payload['usage'], flush=True)
    except Exception as e:
        print('ERROR', name, type(e).__name__, str(e)[:500], flush=True)
print('ALL DONE')
