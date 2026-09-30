"""Run the explicitly approved plans, saving one result per asset without rerolls."""
import concurrent.futures
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/route-landmarks'
plans = json.loads((OUT / 'dry-run-plans.json').read_text())
selected = set(sys.argv[1:])
if not selected:
    raise SystemExit('Provide explicit place IDs from the approved plan.')

def run(plan):
    pid = plan['id']
    result_path = OUT / (pid + '-result.json')
    if result_path.exists():
        print(pid, 'already attempted; inspect saved result before any retry', flush=True)
        return
    print(pid, 'starting approved generation', flush=True)
    with (OUT / (pid + '-progress.log')).open('w') as log:
        p = subprocess.run(plan['command'] + ['--yes', '--json'], cwd=ROOT,
                           stdout=subprocess.PIPE, stderr=log, text=True)
    try:
        result = json.loads(p.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        result = {'stdout': p.stdout}
    result['cli_exit_code'] = p.returncode
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(pid, 'exit', p.returncode, 'status', result.get('status'),
          'credits', result.get('credits_consumed'), flush=True)

with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    list(pool.map(run, [p for p in plans if p['id'] in selected]))
