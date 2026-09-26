"""Frozen-revision Stage4 reviewer orchestration; evidence only, no source writes."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import urllib.request

ROOT=Path(__file__).resolve().parent
REPO=Path('/Volumes/FIGUEIRA/LABLAB/BAND DARK FACTORY/submission-tablekeeper')
OFFICIAL=Path('/Volumes/FIGUEIRA/LABLAB/BAND DARK FACTORY/official-dark-factory-wearedevs')
DOCKER='/Applications/Docker.app/Contents/Resources/bin/docker'
PYTHON='/Users/athvs/.cache/figueira-band-harness/bin/python'
STAGE1='0050accbdc6d0457ffdc73de6365158e65c1808b'
STAGE2='2ebbd48a3ba2b6de7eba2a5fcd851a36efc4e2c8'

def program(browser=False,selected=None):
    modules=['reviewer_inherited','reviewer_pair_checks','reviewer_policy_checks','reviewer_upgrade_checks','reviewer_closure_oracle','reviewer_replan_checks','reviewer_series_amend_checks','reviewer_final_upgrade_checks']+(['reviewer_browser_checks'] if browser else [])
    lines=['import types,sys,unittest,json']
    for name in modules:
        lines+=['m=types.ModuleType('+repr(name)+');sys.modules['+repr(name)+']=m',
                'exec(compile('+repr((ROOT/(name+'.py')).read_text())+','+repr(name)+',"exec"),m.__dict__)']
    classes=['reviewer_browser_checks.BrowserChecks'] if browser else ['reviewer_inherited.SpecChecks','reviewer_pair_checks.PairChecks','reviewer_policy_checks.PolicyChecks','reviewer_upgrade_checks.UpgradeChecks','reviewer_replan_checks.ReplanChecks','reviewer_series_amend_checks.SeriesAmendChecks','reviewer_final_upgrade_checks.FinalUpgradeChecks']
    lines+=['suite=unittest.TestSuite()']
    for name in selected or classes:
        lines+=['suite.addTests(unittest.defaultTestLoader.loadTestsFromName('+repr(name)+'))']
    lines+=['result=unittest.TextTestRunner(verbosity=2).run(suite)',
            'from reviewer_inherited import METRICS',
            'normal=[t for _,p,_,t in METRICS if not p.startswith("/_test/")]',
            'controls=[t for _,p,_,t in METRICS if p.startswith("/_test/")]',
            'print(json.dumps(dict(groups_run=result.testsRun,failures=len(result.failures),errors=len(result.errors),http_requests=len(METRICS),normal_max_seconds=max(normal,default=0),test_control_max_seconds=max(controls,default=0),observed_5xx=sum(s>=500 for _,_,s,_ in METRICS)),sort_keys=True))',
            'sys.exit(0 if result.wasSuccessful() else 1)']
    return '\n'.join(lines)

def main():
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['official','api','browser','package']);p.add_argument('name');p.add_argument('--revision',required=True);p.add_argument('--stage3-tree',required=True);p.add_argument('--stage4-tree');p.add_argument('--tests',nargs='*');args=p.parse_args()
    if args.mode=='package':p.error('--stage4-tree required for final package') if not args.stage4_tree else None
    out=ROOT/args.name;out.mkdir(exist_ok=False)
    env=dict(os.environ,PATH=str(Path(DOCKER).parent)+':'+str(Path(PYTHON).parent)+':'+os.environ.get('PATH',''),PYTHONDONTWRITEBYTECODE='1')
    metadata=dict(stage=4,mode=args.mode,revision=args.revision,started_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),commands=[])
    def cmd(argv,name,cwd=REPO,check=True,input_text=None):
        start=time.monotonic()
        r=subprocess.run(argv,cwd=cwd,env=env,input=input_text,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        output=[]
        for line in r.stdout.splitlines():
            if 'REVIEW_SCREENSHOT ' in line:
                prefix,screenshot=line.split('REVIEW_SCREENSHOT ',1)
                if prefix:output.append(prefix)
                label,data=screenshot.split(' ',1)
                assert label.replace('-','').isalnum()
                (out/(label+'.png')).write_bytes(base64.b64decode(data));output.append('screenshot: '+label+'.png')
            else:output.append(line)
        (out/(name+'.log')).write_text('\n'.join(output)+'\n')
        metadata['commands'].append(dict(argv=list(map(str,argv)),cwd=str(cwd),exit=r.returncode,seconds=time.monotonic()-start,log=name+'.log'))
        print(name,'exit',r.returncode,'seconds',round(metadata['commands'][-1]['seconds'],3),flush=True)
        if check and r.returncode:raise RuntimeError(name+' failed; inspect preserved log')
        return r
    start=time.monotonic()
    try:
        assert cmd(['git','rev-parse','HEAD'],'revision').stdout.strip()==args.revision
        assert not cmd(['git','status','--porcelain'],'status-before').stdout.strip(),'Refuse dirty tree'
        assert cmd(['git','rev-parse','HEAD:stage-1'],'stage1-tree').stdout.strip()==STAGE1
        assert cmd(['git','rev-parse','HEAD:stage-2'],'stage2-tree').stdout.strip()==STAGE2
        assert cmd(['git','rev-parse','HEAD:stage-3'],'stage3-tree').stdout.strip()==args.stage3_tree
        metadata['stage3_tree']=args.stage3_tree
        metadata['stage4_tree']=cmd(['git','rev-parse','HEAD:stage-4'],'stage4-tree').stdout.strip()
        if args.stage4_tree:assert metadata['stage4_tree']==args.stage4_tree
        metadata['test_hashes']={}
        for name in ['reviewer_inherited.py','reviewer_pair_checks.py','reviewer_browser_checks.py','reviewer_policy_checks.py','reviewer_upgrade_checks.py','reviewer_run.py','reviewer_closure_oracle.py','reviewer_replan_checks.py','reviewer_series_amend_checks.py','reviewer_final_upgrade_checks.py']:
            shutil.copy2(ROOT/name,out/name);metadata['test_hashes'][name]=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
        if args.mode in ('official','package'):
            adapter=ROOT/'reviewer-docker-bin/docker';env['PATH']=str(adapter.parent)+':'+env['PATH']
            shutil.copy2(adapter,out/'reviewer-docker-adapter.py');metadata['adapter_sha256']=hashlib.sha256(adapter.read_bytes()).hexdigest()
            selection=['--all'] if args.mode=='package' else ['--stage','4']
            r=cmd([PYTHON,'-m','harness','run','--track','tablekeeper','--repo',str(REPO),*selection,'--mode','isolated','--out',str(out/'harness')],'official',cwd=OFFICIAL,check=False)
            metadata['exit']=r.returncode
        else:
            image='reviewer-tablekeeper-s4:'+args.revision[:12];oldimage='reviewer-tablekeeper-s1:0f96bf0cd889'
            cmd([DOCKER,'build','-t',image,'.'],'build-stage4',cwd=REPO/'stage-4')
            cmd([DOCKER,'build','-t',oldimage,'.'],'build-stage1',cwd=REPO/'stage-1')
            oldimage2='reviewer-tablekeeper-s2:2e026c006569'
            cmd([DOCKER,'build','-t',oldimage2,'.'],'build-stage2',cwd=REPO/'stage-2')
            oldimage3='reviewer-tablekeeper-s3:'+args.stage3_tree[:12]
            cmd([DOCKER,'build','-t',oldimage3,'.'],'build-stage3',cwd=REPO/'stage-3')
            network='reviewer-s4-'+args.name;names=[network+'-source',network+'-destination',network+'-old',network+'-old2',network+'-old3']
            cmd([DOCKER,'network','create','--internal',network],'network-create')
            try:
                metadata['health_seconds']=[]
                for i,name in enumerate(names):
                    internal=8097 if i==1 else 8080
                    argv=[DOCKER,'run','-d','--rm','--name',name,'--network',network,'--cpus=2','--memory=2g']
                    if i==1:argv+=['-e','PORT=8097']
                    launched=time.monotonic();cmd(argv+[oldimage if i==2 else oldimage2 if i==3 else oldimage3 if i==4 else image],'start-'+str(i))
                    code="import urllib.request,json,time\nd=time.monotonic()+55\nwhile True:\n try:\n  r=urllib.request.urlopen('http://127.0.0.1:"+str(internal)+"/health',timeout=2);assert r.status==200 and json.load(r)=={'status':'ok'};break\n except Exception:\n  if time.monotonic()>d:raise\n  time.sleep(.1)"
                    cmd([DOCKER,'exec',name,'python','-c',code],'health-'+str(i))
                    metadata['health_seconds'].append(time.monotonic()-launched)
                    cmd([DOCKER,'inspect','--format','{{.HostConfig.NanoCpus}} {{.HostConfig.Memory}} {{.HostConfig.NetworkMode}} {{json .Mounts}}',name],'constraints-'+str(i))
                cmd([DOCKER,'network','inspect','--format','{{.Internal}}',network],'network-internal')
                code="import socket\ns=socket.socket();s.settimeout(1)\ntry:\n s.connect(('1.1.1.1',443));raise SystemExit('OUTBOUND_CONNECTED')\nexcept OSError: print('outbound unavailable as required')"
                cmd([DOCKER,'exec',names[0],'python','-c',code],'outbound-probe')
                client='df-harness-runner' if args.mode=='browser' else image
                argv=[DOCKER,'run','--rm','-i','--network',network,'--cpus=2','--memory=2g',
                      '-e','REVIEW_BASE=http://'+names[0]+':8080','-e','REVIEW_DEST=http://'+names[1]+':8097',
                      '-e','REVIEW_OLD=http://'+names[2]+':8080','-e','REVIEW_OLD2=http://'+names[3]+':8080','-e','REVIEW_OLD3=http://'+names[4]+':8080','--entrypoint','python',client,'-B','-']
                r=cmd(argv,'checks',check=False,input_text=program(args.mode=='browser',args.tests));metadata['exit']=r.returncode
            finally:
                for i,name in enumerate(names):cmd([DOCKER,'rm','-f',name],'cleanup-'+str(i),check=False)
                cmd([DOCKER,'network','rm',network],'network-remove',check=False)
            smoke=network+'-runmd';launched=time.monotonic()
            cmd([DOCKER,'run','-d','--rm','--name',smoke,'--cpus=2','--memory=2g','-e','PORT=8080','-p','127.0.0.1:18095:8080',image],'runmd-start')
            try:
                while True:
                    try:
                        with urllib.request.urlopen('http://127.0.0.1:18095/health',timeout=2) as response:
                            assert response.status==200 and json.load(response)=={'status':'ok'}
                        break
                    except Exception:
                        if time.monotonic()-launched>60:raise
                        time.sleep(.1)
                metadata['runmd_health_seconds']=time.monotonic()-launched
            finally:cmd([DOCKER,'rm','-f',smoke],'runmd-cleanup',check=False)
        assert cmd(['git','rev-parse','HEAD'],'final-revision').stdout.strip()==args.revision
        assert cmd(['git','rev-parse','HEAD:stage-1'],'final-stage1-tree').stdout.strip()==STAGE1
        assert cmd(['git','rev-parse','HEAD:stage-2'],'final-stage2-tree').stdout.strip()==STAGE2
        assert cmd(['git','rev-parse','HEAD:stage-3'],'final-stage3-tree').stdout.strip()==args.stage3_tree
        assert not cmd(['git','status','--porcelain'],'status-after').stdout.strip()
    finally:
        metadata['elapsed_seconds']=time.monotonic()-start
        (out/'reviewer-run.json').write_text(json.dumps(metadata,indent=2)+'\n')
    return metadata.get('exit',1)

if __name__=='__main__':sys.exit(main())
