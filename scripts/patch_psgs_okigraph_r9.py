#!/usr/bin/env python3
"""Build Print Shop GS OkiGraph-I R9 directly from a known original .2mg.

R9 is the first geometry-corrected build after the hardware-good R8 baseline.
It is intentionally self-contained: no earlier patcher is required.

The private selected-printer block implements the R8 persistent OkiGraph state:
  * first graphics row enters data state with ETX ($03);
  * later rows do not re-enter graphics;
  * literal raster $03 remains escaped as $03 $03 by PSGS encoder metadata;
  * every active graphics vertical movement emits exactly $03 $0E and remains
    in graphics;
  * horizontal graphics remain seven-pin / 60 columns per inch.

R9 adds exact vertical compensation for OkiGraph I's physical 15/144-inch band
origin versus PSGS's logical 14/144-inch seven-row model.  PSGS already has a
vertical phase-table resampler.  R9 expresses the correction as 70/75 = 14/15:
  * private Oki descriptor Y word: 72 -> 70;
  * both vertical table generator bases in MF: 72 -> 75.

The stock scaler therefore produces the repeating phase schedule:
  1 1 1 1 1 1 1 0 1 1 1 1 1 1 1
which emits fourteen vertical rows per fifteen logical rows.

This remains an OkiGraph-specific test build after selecting "82A83A OGI";
the two direct MF helper calls assume the private page-3 block is resident.
"""
from pathlib import Path
import argparse, hashlib, struct

B=512; EL=39; EPB=13
MF_LOAD=0x0800
ORIG_PR_SHA='09e51f041e67fa58756c0c32a362bcff7119488af5070df884f4778fff86e3e0'
ORIG_MF_SHA='12b35bc7e4bfa08268399a2b8ef65750230ff8625f72302106677594977ff7e3'
OLD_NAME=b'Okidata 84'; NEW_NAME=b'82A83A OGI'; NAME_OFF=0x0230
OLD_DESC_OFF=0x0782; OLD_NEXT_DESC=0x07A4
APPEND_OFF=0x0A05; BLOCK_LEN=0x80; NEW_EOF=APPEND_OFF+BLOCK_LEN
LIVE_BASE=0x0300; BEGIN_HELP=0x0330; VERT_HELP=0x0341; STATE=0x037E

OLD_ML84=bytes.fromhex(
 '00 00 00 07 3c 00 48 00 3f 00 00 01 0d 03 1b 25 '
 '39 81 01 0a 00 00 01 02 1e 03 02 03 02 03 02 03 03 02')
assert len(OLD_ML84)==34 and OLD_DESC_OFF+len(OLD_ML84)==OLD_NEXT_DESC

DESC=bytes.fromhex(
 '00 ' '00 00 ' '07 ' '3c 00 ' '46 00 ' '3f ' '00 ' '00 ' '00 '
 '03 1b 25 39 ' '81 ' '01 0a ' '00 ' '00 ' '01 ' '01 03 ' '00 '
 '03 ' '02 03 03 ' '02'
)
assert len(DESC)==30

BEGIN_CODE=bytes.fromhex(
 '48 ' 'ad 7e 03 ' 'd0 07 ' 'ee 7e 03 ' '68 ' '4c fa 77 '
 '68 ' '4c 71 77'
)
assert len(BEGIN_CODE)==17

VERT_CODE=bytes.fromhex(
 '48 ' 'ae 7e 03 ' 'f0 0e '
 'a9 03 00 20 e4 73 '
 'a9 0e 00 20 e4 73 '
 '68 60 '
 '68 ' 'cd 61 78 ' '4c ca 75'
)
assert len(VERT_CODE)==27 and VERT_HELP+len(VERT_CODE)<=STATE

PRIVATE=bytearray(BLOCK_LEN)
PRIVATE[:len(DESC)]=DESC
PRIVATE[BEGIN_HELP-LIVE_BASE:BEGIN_HELP-LIVE_BASE+len(BEGIN_CODE)]=BEGIN_CODE
PRIVATE[VERT_HELP-LIVE_BASE:VERT_HELP-LIVE_BASE+len(VERT_CODE)]=VERT_CODE
PRIVATE[STATE-LIVE_BASE:STATE-LIVE_BASE+2]=b'\x00\x00'
PRIVATE=bytes(PRIVATE)

BEGIN_CALL_OFF=0x7686-MF_LOAD
VERT_ENTRY_OFF=0x75C7-MF_LOAD
OLD_BEGIN_CALL=bytes.fromhex('20 fa 77')
NEW_BEGIN_CALL=bytes.fromhex('20 30 03')
OLD_VERT_ENTRY=bytes.fromhex('cd 61 78')
NEW_VERT_ENTRY=bytes.fromhex('4c 41 03')

VERT_BASE1_OFF=0x7541-MF_LOAD
VERT_BASE2_OFF=0x758C-MF_LOAD
OLD_VERT_BASE=bytes.fromhex('a2 48 00')
NEW_VERT_BASE=bytes.fromhex('a2 4b 00')

def phase_table(base:int,value:int):
    phase=0; out=[]; half=base//2
    for _ in range(65536):
        count=0; phase=(phase+value)&0xffff
        while True:
            diff=(phase-half)&0xffff
            if (diff&0x8000) or diff==0: break
            count+=1; phase=(phase-base)&0xffff
        out.append(count)
        if phase==0: return out
    raise RuntimeError('phase table did not terminate')

EXPECTED_PHASE=[1,1,1,1,1,1,1,0,1,1,1,1,1,1,1]
assert phase_table(75,70)==EXPECTED_PHASE
assert len(EXPECTED_PHASE)==15 and sum(EXPECTED_PHASE)==14

def sha(x): return hashlib.sha256(x).hexdigest()
def u16(x,o): return x[o]|x[o+1]<<8
def u24(x,o): return x[o]|x[o+1]<<8|x[o+2]<<16
def p24(x,o,v): x[o:o+3]=bytes((v&255,(v>>8)&255,(v>>16)&255))

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
    off=4+i*EL; e=bytes(d[off:off+EL]); l=e[0]&15; st=e[0]>>4
    if l and st and e[1:1+l].decode('ascii','replace').upper()==w.upper():
     return {'st':st,'key':u16(e,17),'eof':u24(e,21),'dirblk':n,'off':off,'blocks_used':u16(e,19)}
   n=nx
  raise RuntimeError(w+' not found')
 def blocks(s,r,eof=None):
  eof=r['eof'] if eof is None else eof; need=(eof+B-1)//B; st=r['st']; k=r['key']
  if st==1: return [k]
  if st==2:
   idx=s.blk(k); out=[]
   for i in range(need):
    n=idx[i]|idx[256+i]<<8
    if not n: raise RuntimeError('sparse sapling file')
    out.append(n)
   return out
  if st==3:
   m=s.blk(k); out=[]
   for j in range((need+255)//256):
    sk=m[j]|m[256+j]<<8
    if not sk: raise RuntimeError('sparse tree index')
    idx=s.blk(sk)
    for i in range(min(256,need-len(out))):
     n=idx[i]|idx[256+i]<<8
     if not n: raise RuntimeError('sparse tree data')
     out.append(n)
   return out
  raise RuntimeError('unsupported storage type')
 def read(s,r): return b''.join(bytes(s.blk(n)) for n in s.blocks(r))[:r['eof']]
 def write_same(s,r,x):
  if len(x)!=r['eof']: raise RuntimeError('size change in write_same')
  for i,n in enumerate(s.blocks(r)):
   c=x[i*B:(i+1)*B]; s.blk(n)[:len(c)]=c
 def grow_within_alloc(s,r,x):
  old=s.blocks(r); need=(len(x)+B-1)//B
  if need!=len(old): raise RuntimeError(f'growth changes data-block count {len(old)}->{need}')
  if len(x)>len(old)*B: raise RuntimeError('growth exceeds allocated blocks')
  for i,n in enumerate(old):
   c=x[i*B:(i+1)*B]; blk=s.blk(n); blk[:len(c)]=c
   if len(c)<B: blk[len(c):]=b'\x00'*(B-len(c))
  ent=s.blk(r['dirblk']); p24(ent,r['off']+21,len(x)); r['eof']=len(x)

def patch(src,dst):
 src=Path(src); dst=Path(dst); d=D(src)
 prrec=d.find('PRDRIVERS'); mfrec=d.find('MF')
 pr=d.read(prrec); mf=d.read(mfrec)
 if sha(pr)!=ORIG_PR_SHA: raise RuntimeError('original PRDRIVERS SHA mismatch: '+sha(pr))
 if sha(mf)!=ORIG_MF_SHA: raise RuntimeError('original MF SHA mismatch: '+sha(mf))
 if len(pr)!=APPEND_OFF: raise RuntimeError(f'unexpected PRDRIVERS EOF ${len(pr):04X}')
 if pr[NAME_OFF:NAME_OFF+10]!=OLD_NAME or pr[NAME_OFF+10:NAME_OFF+14]!=bytes.fromhex('00 00 82 07'):
  raise RuntimeError('stock ML84 selector mismatch')
 if pr[OLD_DESC_OFF:OLD_NEXT_DESC]!=OLD_ML84: raise RuntimeError('stock ML84 descriptor mismatch')
 if mf[BEGIN_CALL_OFF:BEGIN_CALL_OFF+3]!=OLD_BEGIN_CALL: raise RuntimeError('MF graphics-begin call mismatch')
 if mf[VERT_ENTRY_OFF:VERT_ENTRY_OFF+3]!=OLD_VERT_ENTRY: raise RuntimeError('MF vertical-entry mismatch')
 if mf[VERT_BASE1_OFF:VERT_BASE1_OFF+3]!=OLD_VERT_BASE or mf[VERT_BASE2_OFF:VERT_BASE2_OFF+3]!=OLD_VERT_BASE:
  raise RuntimeError('MF vertical table base mismatch')

 ctx1=bytes.fromhex('ad 64 a0 85 08 a8 a2 48 00 a9 4d 79 20 43 79')
 if mf[0x753B-MF_LOAD:0x753B-MF_LOAD+len(ctx1)]!=ctx1:
  raise RuntimeError('first vertical-resampler context mismatch')
 ctx2=bytes.fromhex('a2 48 00 a4 08 a9 4d 79 20 43 79')
 if mf[0x758C-MF_LOAD:0x758C-MF_LOAD+len(ctx2)]!=ctx2:
  raise RuntimeError('second vertical-resampler context mismatch')
 horiz=bytes.fromhex('a2 78 00 a9 e9 73 4c 43 79')
 if mf[0x75A2-MF_LOAD:0x75A2-MF_LOAD+len(horiz)]!=horiz:
  raise RuntimeError('horizontal 120-dpi scaler context mismatch')

 q=bytearray(pr)
 q[NAME_OFF:NAME_OFF+10]=NEW_NAME
 q[NAME_OFF+12:NAME_OFF+14]=bytes((APPEND_OFF&255,APPEND_OFF>>8))
 q.extend(PRIVATE)
 if q[OLD_DESC_OFF:OLD_NEXT_DESC]!=OLD_ML84: raise RuntimeError('stock ML84 changed')
 if q[0x03D6:0x0411]!=pr[0x03D6:0x0411]: raise RuntimeError('stock ML92/93 shared descriptor changed')

 m=bytearray(mf)
 m[BEGIN_CALL_OFF:BEGIN_CALL_OFF+3]=NEW_BEGIN_CALL
 m[VERT_ENTRY_OFF:VERT_ENTRY_OFF+3]=NEW_VERT_ENTRY
 m[VERT_BASE1_OFF:VERT_BASE1_OFF+3]=NEW_VERT_BASE
 m[VERT_BASE2_OFF:VERT_BASE2_OFF+3]=NEW_VERT_BASE

 md=[i for i,(a,b) in enumerate(zip(mf,m)) if a!=b]
 expected=sorted([
   BEGIN_CALL_OFF+1, BEGIN_CALL_OFF+2,
   VERT_ENTRY_OFF, VERT_ENTRY_OFF+1, VERT_ENTRY_OFF+2,
   VERT_BASE1_OFF+1, VERT_BASE2_OFF+1,
 ])
 if md!=expected: raise RuntimeError('unexpected MF diff scope: '+repr(md))

 d.grow_within_alloc(prrec,bytes(q)); d.write_same(mfrec,bytes(m))
 dst.parent.mkdir(parents=True,exist_ok=True); dst.write_bytes(d.r)

 c=D(dst); cpr=c.read(c.find('PRDRIVERS')); cmf=c.read(c.find('MF'))
 if cpr!=bytes(q): raise RuntimeError('post-write PRDRIVERS verify failed')
 if cmf!=bytes(m): raise RuntimeError('post-write MF verify failed')
 if cpr[APPEND_OFF:NEW_EOF]!=PRIVATE: raise RuntimeError('private R9 block mismatch')
 if cmf[BEGIN_CALL_OFF:BEGIN_CALL_OFF+3]!=NEW_BEGIN_CALL: raise RuntimeError('begin helper call missing')
 if cmf[VERT_ENTRY_OFF:VERT_ENTRY_OFF+3]!=NEW_VERT_ENTRY: raise RuntimeError('vertical helper call missing')
 if cmf[VERT_BASE1_OFF:VERT_BASE1_OFF+3]!=NEW_VERT_BASE or cmf[VERT_BASE2_OFF:VERT_BASE2_OFF+3]!=NEW_VERT_BASE:
  raise RuntimeError('14/15 vertical table base missing')
 if cmf[0x75A2-MF_LOAD:0x75A2-MF_LOAD+len(horiz)]!=horiz:
  raise RuntimeError('horizontal scaler changed')

 before=src.read_bytes(); after=dst.read_bytes()
 if len(before)!=len(after): raise RuntimeError('disk image size changed')
 diffs=[i for i,(a,b) in enumerate(zip(before,after)) if a!=b]
 print('source disk    :',src)
 print('source sha     :',sha(before))
 print('output R9 disk :',dst)
 print('output sha     :',sha(after))
 print('PRDRIVERS R9   :',sha(cpr),len(cpr),'bytes')
 print('MF R9          :',sha(cmf),len(cmf),'bytes')
 print('vertical ratio : 70/75 = 14/15 = %.9f'%(70/75))
 print('phase table    :',' '.join(map(str,EXPECTED_PHASE)),'sum=14/15')
 print('horizontal     : unchanged 120->60 PSGS reducer')
 print('disk diffs     :',len(diffs),'physical bytes vs original')
 print('MF caves used  : NONE')
 print('WARNING        : select 82A83A OGI before printing; direct MF helper calls are Oki-specific')

def main():
 ap=argparse.ArgumentParser()
 ap.add_argument('input',type=Path,help='known original PSGS .2mg')
 ap.add_argument('output',type=Path,help='R9 .2mg output')
 a=ap.parse_args(); patch(a.input,a.output)

if __name__=='__main__': main()
