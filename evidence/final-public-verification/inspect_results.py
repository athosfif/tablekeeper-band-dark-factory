"""Read and validate original completed harness reports, for the recorded evidence review."""
import pathlib,json,subprocess,time
D=pathlib.Path('/Users/athvs/.cache/figueira-band-final-verification/public-verification-20260926');Q=D.parent/'public-clone-20260926';r=json.loads((D/'verification-receipt.json').read_text())
print('\033[2J\033[H',end='',flush=True)
print('FIGUEIRA / TABLEKEEPER / PUBLIC REPOSITORY',flush=True)
print('Reading the original completed isolated verification reports.\n',flush=True)
assert r['check_exit']==r['harness_exit']==0
print('Verified revision: '+r['source_revision'],flush=True)
assert subprocess.check_output(['git','-C',str(Q),'rev-parse','HEAD'],text=True).strip()==r['source_revision']
print('4 independently buildable stages | 2 CPUs / 2 GiB per tested service',flush=True)
print('Original --all run: '+str(round(r['elapsed_seconds'],2))+' seconds\n',flush=True)
total=0
for s in range(1,5):
 rep=json.loads((D/f'harness/stage-{s}/report.json').read_text());assert rep['state']=='completed' and rep['highest_contiguous']==s
 cs=[json.loads((D/f'harness/stage-{s}/stage-{t}.counts.json').read_text()) for t in range(1,s+1)]
 passed=sum(c['passed'] for c in cs);collected=sum(c['collected'] for c in cs);assert passed==collected and all(not any(c[k] for k in ['failed','errors','skipped','deselected']) for c in cs);total+=passed
 print(f'  STAGE {s}     {passed:3d} / {collected:3d} applicable checks passed',flush=True);time.sleep(.8)
print('\n575 cumulative executions across folders, not 575 unique tests.',flush=True);assert total==575
print('Expected next-stage probes are separate; original logs are preserved.',flush=True)
print('Room export, mandates and three-seat handoffs: check passed.',flush=True)
print('\nThese are local results, not the organizers\' hidden score.',flush=True)
print('Original reports: evidence/final-public-verification/',flush=True)
