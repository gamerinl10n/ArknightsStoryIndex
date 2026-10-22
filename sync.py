"""Fetch a pinned upstream snapshot before importing; failed fetch leaves active DB intact."""
import argparse
import subprocess
from pathlib import Path
from core import connect, ingest

p=argparse.ArgumentParser()
p.add_argument('--checkout',default='data/upstream')
p.add_argument('--database',default='data/index.sqlite')
p.add_argument('--ref',default='master')
a=p.parse_args()
root=Path(a.checkout)
root.parent.mkdir(parents=True,exist_ok=True)
url='https://github.com/ArknightsAssets/ArknightsGamedata.git'
def git(*args):
    return subprocess.check_output(['git','-C',str(root),*args],text=True).strip()
if not (root/'.git').exists():
    subprocess.run(['git','clone','--depth=1','--filter=blob:none','--no-checkout',url,str(root)],check=True)
    git('sparse-checkout','set','kr/gamedata/story','cn/gamedata/story')
git('fetch','origin',a.ref,'--depth=1')
revision=git('rev-parse','FETCH_HEAD')
git('checkout','--detach',revision)
Path(a.database).parent.mkdir(parents=True,exist_ok=True)
with connect(a.database) as db:
    print(ingest(db,root,revision,'ArknightsAssets/ArknightsGamedata'), 'lines imported at',revision)
