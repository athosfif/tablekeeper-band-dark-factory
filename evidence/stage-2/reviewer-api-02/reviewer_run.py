"""Frozen-revision Stage2 reviewer orchestration; evidence only, no source writes."""
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

def program(browser=False,selected=None):
    modules=['reviewer_inherited','reviewer_pair_checks']+(['reviewer_browser_checks'] if browser else [])
    lines=['import types,sys,unittest,json']
    for name in modules:
        lines+=['m=types.ModuleType('+repr(name)+');sys.modules['+repr(name)+']=m',
                'exec(compile('+repr((ROOT/(name+'.py')).read_text())+','+repr(name)+',"exec"),m.__dict__)']
    classes=['reviewer_browser_checks.BrowserChecks'] if browser else ['reviewer_inherited.SpecChecks','reviewer_pair_checks.PairChecks']
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
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['official','api','browser']);p.add_argument('name');p.add_argument('--revision',required=True);p.add_argument('--tests',nargs='*');args=p.parse_args()
    out=ROOT/args.name;out.mkdir(exist_ok=False)
    env=dict(os.environ,PATH=str(Path(DOCKER).parent)+':'+str(Path(PYTHON).parent)+':'+os.environ.get('PATH',''),PYTHONDONTWRITEBYTECODE='1')
    metadata=dict(stage=2,mode=args.mode,revision=args.revision,started_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),commands=[])
    def cmd(argv,name,cwd=REPO,check=True,input_text=None):
        start=time.monotonic()
        r=subprocess.run(argv,cwd=cwd,env=env,input=input_text,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        output=[]
        for line in r.stdout.splitlines():
            if line.startswith('REVIEW_SCREENSHOT '):
                _,label,data=line.split(' ',2)
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
        metadata['stage2_tree']=cmd(['git','rev-parse','HEAD:stage-2'],'stage2-tree').stdout.strip()
        metadata['test_hashes']={}
        for name in ['reviewer_inherited.py','reviewer_pair_checks.py','reviewer_browser_checks.py','reviewer_run.py']:
            shutil.copy2(ROOT/name,out/name);metadata['test_hashes'][name]=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
        if args.mode=='official':
            adapter=ROOT/'reviewer-docker-bin/docker';env['PATH']=str(adapter.parent)+':'+env['PATH']
            shutil.copy2(adapter,out/'reviewer-docker-adapter.py');metadata['adapter_sha256']=hashlib.sha256(adapter.read_bytes()).hexdigest()
            r=cmd([PYTHON,'-m','harness','run','--track','tablekeeper','--repo',str(REPO),'--stage','2','--mode','isolated','--out',str(out/'harness')],'official',cwd=OFFICIAL,check=False)
            metadata['exit']=r.returncode
        else:
            image='reviewer-tablekeeper-s2:'+args.revision[:12];oldimage='reviewer-tablekeeper-s1:0f96bf0cd889'
            cmd([DOCKER,'build','-t',image,'.'],'build-stage2',cwd=REPO/'stage-2')
            cmd([DOCKER,'build','-t',oldimage,'.'],'build-stage1',cwd=REPO/'stage-1')
            network='reviewer-s2-'+args.name;names=[network+'-source',network+'-destination',network+'-old']
            cmd([DOCKER,'network','create','--internal',network],'network-create')
            try:
                metadata['health_seconds']=[]
                for i,name in enumerate(names):
                    internal=8097 if i==1 else 8080
                    argv=[DOCKER,'run','-d','--rm','--name',name,'--network',network,'--cpus=2','--memory=2g']
                    if i==1:argv+=['-e','PORT=8097']
                    launched=time.monotonic();cmd(argv+[oldimage if i==2 else image],'start-'+str(i))
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
                      '-e','REVIEW_OLD=http://'+names[2]+':8080','--entrypoint','python',client,'-B','-']
                r=cmd(argv,'checks',check=False,input_text=program(args.mode=='browser',args.tests));metadata['exit']=r.returncode
            finally:
                for i,name in enumerate(names):cmd([DOCKER,'rm','-f',name],'cleanup-'+str(i),check=False)
                cmd([DOCKER,'network','rm',network],'network-remove',check=False)
            smoke=network+'-runmd';launched=time.monotonic()
            cmd([DOCKER,'run','-d','--rm','--name',smoke,'--cpus=2','--memory=2g','-e','PORT=8080','-p','127.0.0.1:18093:8080',image],'runmd-start')
            try:
                while True:
                    try:
                        with urllib.request.urlopen('http://127.0.0.1:18093/health',timeout=2) as response:
                            assert response.status==200 and json.load(response)=={'status':'ok'}
                        break
                    except Exception:
                        if time.monotonic()-launched>60:raise
                        time.sleep(.1)
                metadata['runmd_health_seconds']=time.monotonic()-launched
            finally:cmd([DOCKER,'rm','-f',smoke],'runmd-cleanup',check=False)
        assert cmd(['git','rev-parse','HEAD'],'final-revision').stdout.strip()==args.revision
        assert cmd(['git','rev-parse','HEAD:stage-1'],'final-stage1-tree').stdout.strip()==STAGE1
        assert not cmd(['git','status','--porcelain'],'status-after').stdout.strip()
    finally:
        metadata['elapsed_seconds']=time.monotonic()-start
        (out/'reviewer-run.json').write_text(json.dumps(metadata,indent=2)+'\n')
    return metadata.get('exit',1)

if __name__=='__main__':sys.exit(main())
