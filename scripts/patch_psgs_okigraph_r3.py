#!/usr/bin/env python3
"""R3: R2 protocol plus per-raster-row reset of PSGS's 120->60 reducer."""
from pathlib import Path
import argparse, contextlib, hashlib, importlib.util, io, struct, tempfile

B=512; EL=39; EPB=13
MFSHA='12b35bc7e4bfa08268399a2b8ef65750230ff8625f72302106677594977ff7e3'
PRR2='fbfed119fcfb2cfcc4d37e2d20453c3b561f7a91faac01be34c1bf4b840112b1'
LOAD=0x800; RO=0x72F9-LOAD; HO=0x7525-LOAD
OLD=bytes.fromhex('9c 07 73'); NEW=bytes.fromhex('20 25 75')
HELP=bytes.fromhex('9c e7 73 9c 69 78 9c 6b 78 60')
def sha(x): return hashlib.sha256(x).hexdigest()
def u16(x,o): return x[o]|x[o+1]<<8
def u24(x,o): return x[o]|x[o+1]<<8|x[o+2]<<16

class D:
 def __init__(s,p):
  s.p=Path(p); s.r=bytearray(s.p.read_bytes())
  if s.r[:4]!=b'2IMG': raise RuntimeError('not 2IMG')
  s.n=struct.unpack_from('<I',s.r,20)[0]; s.o=struct.unpack_from('<I',s.r,24)[0]
 def blk(s,n): a=s.o+n*B; return memoryview(s.r)[a:a+B]
 def find(s,w):
  n=2; seen=set()
  while n and n not in seen:
   seen.add(n); d=s.blk(n); nx=u16(d,2)
   for i in range(EPB):
    e=bytes(d[4+i*EL:4+(i+1)*EL]); l=e[0]&15; st=e[0]>>4
    if l and st and e[1:1+l].decode('ascii','replace').upper()==w.upper(): return st,u16(e,17),u24(e,21)
   n=nx
  raise RuntimeError(w+' not found')
 def blocks(s,r):
  st,k,eof=r; need=(eof+B-1)//B
  if st==1: return [k]
  if st==2:
   x=s.blk(k); return [x[i]|x[256+i]<<8 for i in range(need)]
  if st==3:
   m=s.blk(k); out=[]
   for j in range((need+255)//256):
    sk=m[j]|m[256+j]<<8; x=s.blk(sk)
    for i in range(min(256,need-len(out))): out.append(x[i]|x[256+i]<<8)
   return out
  raise RuntimeError('unsupported storage')
 def read(s,r): return b''.join(bytes(s.blk(n)) for n in s.blocks(r))[:r[2]]
 def write(s,r,x):
  if len(x)!=r[2]: raise RuntimeError('size change')
  for i,n in enumerate(s.blocks(r)):
   c=x[i*B:(i+1)*B]; s.blk(n)[:len(c)]=c

def r2mod():
 p=Path(__file__).resolve().parent/'patch_psgs_okigraph_r2.py'; sp=importlib.util.spec_from_file_location('r2',p)
 if not p.exists() or sp is None or sp.loader is None: raise RuntimeError('R2 patcher missing')
 m=importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m

def patch(src,dst):
 src=Path(src); dst=Path(dst)
 with tempfile.TemporaryDirectory() as td:
  t=Path(td)/'r2.2mg'
  with contextlib.redirect_stdout(io.StringIO()): r2mod().patch(src,t)
  d=D(t); pr=d.read(d.find('PRDRIVERS'))
  if sha(pr)!=PRR2: raise RuntimeError('R2 PRDRIVERS mismatch')
  mr=d.find('MF'); mf=d.read(mr)
  if sha(mf)!=MFSHA or mf[RO:RO+3]!=OLD or mf[HO:HO+len(HELP)]!=HELP: raise RuntimeError('MF baseline mismatch')
  q=bytearray(mf); q[RO:RO+3]=NEW
  if [i for i,(a,b) in enumerate(zip(mf,q)) if a!=b]!=[RO,RO+1,RO+2]: raise RuntimeError('MF diff scope')
  d.write(mr,bytes(q)); dst.parent.mkdir(parents=True,exist_ok=True); dst.write_bytes(d.r)
 c=D(dst); cm=c.read(c.find('MF')); cp=c.read(c.find('PRDRIVERS'))
 if cm!=bytes(q) or sha(cp)!=PRR2: raise RuntimeError('post-write verify failed')
 a=src.read_bytes(); z=dst.read_bytes(); dd=sum(x!=y for x,y in zip(a,z))
 if len(a)!=len(z) or dd!=30: raise RuntimeError('unexpected disk diff scope')
 print('source sha  :',sha(a)); print('output sha  :',sha(z)); print('PRDRIVERS   :',sha(cp)); print('MF          :',MFSHA,'->',sha(cm)); print('row setup   : $72F9 STZ $7307 -> JSR $7525'); print('disk diffs  :',dd)

def main():
 a=argparse.ArgumentParser(); a.add_argument('input',type=Path); a.add_argument('output',type=Path); x=a.parse_args(); patch(x.input,x.output)
if __name__=='__main__': main()
