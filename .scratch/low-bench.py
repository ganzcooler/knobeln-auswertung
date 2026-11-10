import json, sys, time
from pathlib import Path
sys.path.insert(0, str(Path('src').resolve()))
from knobeln.llm.client import OpenRouterClient

def load_key():
    for line in Path('.env').read_text().splitlines():
        if line.strip().startswith('OPENROUTER_API_KEY='):
            return line.split('=',1)[1].strip().strip('"').strip("'")
    raise SystemExit('no key')

name = sys.argv[1]
stem = Path(name).stem
key = load_key()
outdir = Path('.scratch/reasoning-bench')
for rep in [1,2]:
    dest = outdir / (f'{stem}_low' + ('' if rep==1 else '_rep2') + '.json')
    if dest.exists():
        print('skip', dest, flush=True); continue
    client = OpenRouterClient(api_key=key, model='deepseek/deepseek-v4.1-flash', reasoning='low', no_cache=True, timeout=900)
    t=time.time(); print('START', name, 'low', 'rep', rep, flush=True)
    try:
        res = client.extract_bogen(bogen_id=f'{stem}-low-rep{rep}', quelle=str(Path('examples')/name), image_bytes=(Path('examples')/name).read_bytes(), mime_type='image/jpeg')
        payload={'image':name,'effort':'low','rep':rep,'elapsed_s':round(time.time()-t,1),'usage':{'prompt_tokens':res.prompt_tokens,'completion_tokens':res.completion_tokens,'reasoning_tokens':res.reasoning_tokens,'cost_usd':res.cost_usd},'bogen':res.bogen.model_dump(mode='json')}
        dest.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
        print('DONE', name, 'low', 'rep', rep, payload['elapsed_s'], 's', payload['usage'], flush=True)
    except Exception as e:
        print('ERROR', name, 'low', 'rep', rep, type(e).__name__, str(e)[:500], flush=True)
print('ALL DONE', name, flush=True)
