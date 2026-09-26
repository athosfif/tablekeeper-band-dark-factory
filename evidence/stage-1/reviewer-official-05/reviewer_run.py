"""Reproducible reviewer runner. Writes evidence only; never writes service state."""
import argparse
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


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('mode',choices=['official','independent']); parser.add_argument('name'); parser.add_argument('--tests',nargs='*',default=[]); args=parser.parse_args()
    out=ROOT/args.name; out.mkdir(exist_ok=False)
    env=dict(os.environ,PATH=str(Path(DOCKER).parent)+':'+str(Path(PYTHON).parent)+':'+os.environ.get('PATH',''),PYTHONDONTWRITEBYTECODE='1')
    metadata=dict(mode=args.mode,started_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),commands=[])
    def cmd(argv,name,cwd=REPO,check=True,input_text=None):
        start=time.monotonic()
        result=subprocess.run(argv,cwd=cwd,env=env,input=input_text,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        (out/(name+'.log')).write_text(result.stdout)
        metadata['commands'].append(dict(argv=list(map(str,argv)),cwd=str(cwd),exit=result.returncode,seconds=time.monotonic()-start,log=name+'.log'))
        print(name,'exit',result.returncode,'seconds',round(metadata['commands'][-1]['seconds'],3),flush=True)
        if check and result.returncode: raise RuntimeError(name+' failed: '+result.stdout[-1500:])
        return result
    def save(): (out/'reviewer-run.json').write_text(json.dumps(metadata,indent=2)+'\n')
    start=time.monotonic()
    try:
        metadata['revision']=cmd(['git','rev-parse','HEAD'],'revision').stdout.strip()
        status=cmd(['git','status','--porcelain'],'status-before').stdout.strip()
        assert not status, 'Refuse uncommitted working tree'
        metadata['test_sha256']=hashlib.sha256((ROOT/'reviewer_spec_checks.py').read_bytes()).hexdigest()
        shutil.copy2(ROOT/'reviewer_spec_checks.py',out/'reviewer_spec_checks.py')
        shutil.copy2(Path(__file__),out/'reviewer_run.py')
        if args.mode=='official':
            adapter=ROOT/'reviewer-docker-bin'/'docker'
            if adapter.exists():
                env['PATH']=str(adapter.parent)+':'+env['PATH']
                metadata['docker_transport_adapter']=str(adapter)
                metadata['adapter_sha256']=hashlib.sha256(adapter.read_bytes()).hexdigest()
                shutil.copy2(adapter,out/'reviewer-docker-adapter.py')
            result=cmd([PYTHON,'-m','harness','run','--track','tablekeeper','--repo',str(REPO),'--stage','1','--mode','isolated','--out',str(out/'harness')],'official',cwd=OFFICIAL,check=False)
            metadata['exit']=result.returncode
        else:
            image='reviewer-tablekeeper:'+metadata['revision'][:12]
            network='reviewer-'+args.name
            names=[network+'-source',network+'-destination']
            cmd([DOCKER,'build','-t',image,'.'],'build',cwd=REPO/'stage-1')
            cmd([DOCKER,'network','create','--internal',network],'network-create')
            try:
                metadata['health_seconds']=[]
                for i,name in enumerate(names):
                    port=18081+i; internal=8080 if i==0 else 8097
                    argv=[DOCKER,'run','-d','--rm','--name',name,'--network',network,'--cpus=2','--memory=2g','-p',f'127.0.0.1:{port}:{internal}']
                    if i: argv+=['-e','PORT=8097']
                    launched=time.monotonic(); cmd(argv+[image],'start-'+str(i))
                    health_code="import urllib.request,json,time\ndeadline=time.monotonic()+55\nwhile True:\n try:\n  r=urllib.request.urlopen('http://127.0.0.1:"+str(internal)+"/health',timeout=2);assert r.status==200 and json.load(r)=={'status':'ok'};break\n except Exception:\n  if time.monotonic()>deadline:raise\n  time.sleep(.1)\n"
                    cmd([DOCKER,'exec',name,'python','-c',health_code],'health-'+str(i))
                    metadata['health_seconds'].append(time.monotonic()-launched)
                    cmd([DOCKER,'inspect','--format','{{.HostConfig.NanoCpus}} {{.HostConfig.Memory}} {{.HostConfig.NetworkMode}} {{json .Mounts}}',name],'constraints-'+str(i))
                cmd([DOCKER,'network','inspect','--format','{{.Internal}}',network],'network-internal')
                probe="import socket\ns=socket.socket();s.settimeout(1)\ntry:\n s.connect(('1.1.1.1',443));print('OUTBOUND_CONNECTED');raise SystemExit(1)\nexcept OSError:\n print('outbound unavailable as required')\n"
                cmd([DOCKER,'exec',names[0],'python','-c',probe],'outbound-probe')
                result=cmd([DOCKER,'run','--rm','-i','--network',network,'--cpus=2','--memory=2g',
                            '-e','REVIEW_BASE=http://'+names[0]+':8080','-e','REVIEW_DEST=http://'+names[1]+':8097',
                            '--entrypoint','python',image,'-B','-','-v',*args.tests],'independent',check=False,
                           input_text=(out/'reviewer_spec_checks.py').read_text())
                metadata['exit']=result.returncode
            finally:
                for i,name in enumerate(names): cmd([DOCKER,'rm','-f',name],'cleanup-'+str(i),check=False)
                cmd([DOCKER,'network','rm',network],'network-remove',check=False)
            # Reproduce RUN.md's ordinary published-port launch separately from
            # isolated acceptance, whose network deliberately hides host ports.
            smoke=network+'-runmd'
            launched=time.monotonic()
            cmd([DOCKER,'run','-d','--rm','--name',smoke,'--cpus=2','--memory=2g',
                 '-e','PORT=8080','-p','127.0.0.1:18083:8080',image],'runmd-start')
            try:
                while True:
                    try:
                        with urllib.request.urlopen('http://127.0.0.1:18083/health',timeout=2) as response:
                            assert response.status==200 and json.load(response)=={'status':'ok'}
                        break
                    except Exception:
                        if time.monotonic()-launched>60:raise
                        time.sleep(.1)
                metadata['runmd_health_seconds']=time.monotonic()-launched
            finally:
                cmd([DOCKER,'rm','-f',smoke],'runmd-cleanup',check=False)
        metadata['final_revision']=cmd(['git','rev-parse','HEAD'],'final-revision').stdout.strip()
        assert metadata['final_revision']==metadata['revision']
        assert not cmd(['git','status','--porcelain'],'status-after').stdout.strip()
    finally:
        metadata['elapsed_seconds']=time.monotonic()-start
        save()
    return metadata.get('exit',1)


if __name__=='__main__': sys.exit(main())
