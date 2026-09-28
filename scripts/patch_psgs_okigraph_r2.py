#!/usr/bin/env python3
"""R2: native 82A/83A OkiGraph-I descriptor, ETX-only graphics entry."""
from pathlib import Path
import argparse, hashlib, struct

B=512; EL=39; EPB=13
PRSHA='09e51f041e67fa58756c0c32a362bcff7119488af5070df884f4778fff86e3e0'
NO=0x230; DP=0x782; NP=0x7A4
OLDNAME=b'Okidata 84'; NEWNAME=b'82A83A OGI'
OLD=bytes.fromhex('00 00 00 07 3c 00 48 00 3f 00 00 01 0d 03 1b 25 39 81 01 0a 00 00 01 02 1e 03 02 03 02 03 02 03 03 02')
# Native movement 03 03 <n> 03 02; gfx begin 03; end 03 02; 03 data -> 03 03.
NEW=bytes.fromhex('00 00 00 07 3c 00 48 00 3f 00 00 01 0d 02 03 03 81 02 03 02 00 00 01 01 03 02 03 02 03 02 03 03 02 00')
assert len(OLD)==len(NEW)==34 and DP+34==NP

def sha(x): return hashlib.sha256(x).hexdigest()
def u16(x,o): return x[o]|x[o+1]<<8
def u24(x,o): return x[o]|x[o+1]<<8|x[o+2]<<16

class D:
 def __init__(s,p):
  s.p=Path(p); s.r=bytearray(s.p.read_bytes())
  if s.r[:4]!=b'2IMG': raise RuntimeError('not 2IMG')
  s.n=struct.unpack_from('<I',s.r,20)[0]; s.o=struct.unpack_from('<I',s.r,24)[0]
 def blk(s,n):
  a=s.o+n*B; return memoryview(s.r)[a:a+B]
 def find(s,w):
  n=2; seen=set()
  while n and n not in seen:
   seen.add(n); d=s.blk(n); nx=u16(d,2)
   for i in range(EPB):
    e=bytes(d[4+i*EL:4+(i+1)*EL]); l=e[0]&15; st=e[0]>>4
    if l and st and e[1:1+l].decode('ascii','replace').upper()==w.upper():
     return st,u16(e,17),u24(e,21)
   n=nx
  raise RuntimeError(w+' not found')
 def blocks(s,rec):
  st,k,eof=rec; need=(eof+B-1)//B
  if st!=2: raise RuntimeError('PRDRIVERS is not sapling')
  x=s.blk(k); out=[]
  for i in range(need):
   n=x[i]|x[256+i]<<8
   if not n: raise RuntimeError('sparse PRDRIVERS')
   out.append(n)
  return out
 def read(s,rec): return b''.join(bytes(s.blk(n)) for n in s.blocks(rec))[:rec[2]]
 def write(s,rec,x):
  if len(x)!=rec[2]: raise RuntimeError('size change')
  for i,n in enumerate(s.blocks(rec)):
   c=x[i*B:(i+1)*B]; s.blk(n)[:len(c)]=c

def patch(src,dst):
 src=Path(src); dst=Path(dst); d=D(src); rec=d.find('PRDRIVERS'); p=d.read(rec)
 if sha(p)!=PRSHA: raise RuntimeError('PRDRIVERS SHA mismatch: '+sha(p))
 if p[NO:NO+10]!=OLDNAME or p[NO+10:NO+14]!=bytes.fromhex('00 00 82 07'): raise RuntimeError('ML84 selector mismatch')
 if p[DP:NP]!=OLD: raise RuntimeError('ML84 descriptor mismatch')
 q=bytearray(p); q[NO:NO+10]=NEWNAME; q[DP:NP]=NEW
 dif=[i for i,(a,b) in enumerate(zip(p,q)) if a!=b]
 if len(dif)!=27: raise RuntimeError('unexpected PRDRIVERS diff count')
 d.write(rec,bytes(q)); dst.parent.mkdir(parents=True,exist_ok=True); dst.write_bytes(d.r)
 c=D(dst); qp=c.read(c.find('PRDRIVERS'))
 if qp!=bytes(q) or qp[DP:NP]!=NEW: raise RuntimeError('post-write verify failed')
 a=src.read_bytes(); z=dst.read_bytes(); dd=[i for i,(x,y) in enumerate(zip(a,z)) if x!=y]
 if len(a)!=len(z) or len(dd)!=27: raise RuntimeError('unexpected disk diff scope')
 print('source sha  :',sha(a)); print('output sha  :',sha(z)); print('PRDRIVERS   :',sha(qp)); print('disk diffs  :',len(dd))

def main():
 a=argparse.ArgumentParser(); a.add_argument('input',type=Path); a.add_argument('output',type=Path); x=a.parse_args(); patch(x.input,x.output)
if __name__=='__main__': main()
