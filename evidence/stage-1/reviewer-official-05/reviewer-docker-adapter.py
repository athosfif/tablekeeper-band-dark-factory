#!/Users/athvs/.cache/figueira-band-harness/bin/python
"""Transport-only adapter for macOS AppleDouble/xattr Docker build failure.

Only the exact official harness context is streamed as a tar. Ordinary files are
byte-for-byte unchanged; ._* metadata is not runtime content and remains untouched
in the source checkout. Every other invocation goes to the supplied Docker CLI.
"""
import io
import os
from pathlib import Path
import subprocess
import sys
import tarfile

docker='/Applications/Docker.app/Contents/Resources/bin/docker'
context=Path('/Volumes/FIGUEIRA/LABLAB/BAND DARK FACTORY/official-dark-factory-wearedevs/harness')
args=sys.argv[1:]
if args and args[0]=='build' and args[-1]==str(context):
    stream=io.BytesIO()
    with tarfile.open(fileobj=stream,mode='w',format=tarfile.USTAR_FORMAT) as archive:
        for path in sorted(context.rglob('*')):
            if any(p.startswith('._') or p=='__pycache__' for p in path.relative_to(context).parts):
                continue
            if path.is_file(): archive.add(path,arcname=str(path.relative_to(context)),recursive=False)
    if '-f' in args:
        at=args.index('-f')
        assert Path(args[at+1])==context/'Dockerfile'
        del args[at:at+2]
    args[-1]='-'
    print('reviewer transport: streaming unchanged official harness files, excluding AppleDouble metadata',file=sys.stderr)
    result=subprocess.run([docker]+args,input=stream.getvalue())
    sys.exit(result.returncode)
os.execv(docker,[docker]+args)
