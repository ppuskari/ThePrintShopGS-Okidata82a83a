#!/usr/bin/env python3
"""R4: quantize PSGS vertical movement to native OkiGraph-I $0E feeds."""
from pathlib import Path
import argparse, contextlib, hashlib, importlib.util, io, tempfile

LOAD=0x0800
MF_OFF=0x75CB-LOAD
MAXLF_OFF=0x0782+8
MF_SHA="12b35bc7e4bfa08268399a2b8ef65750230ff8625f72302106677594977ff7e3"
PR_R2_SHA="fbfed119fcfb2cfcc4d37e2d20453c3b561f7a91faac01be34c1bf4b840112b1"

def sha(x): return hashlib.sha256(x).hexdigest()

def load(name):
    p=Path(__file__).resolve().parent/name
    s=importlib.util.spec_from_file_location(name,p)
    if not p.exists() or s is None or s.loader is None:
        raise RuntimeError("required sibling missing: "+str(p))
    m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

def patch(src,dst):
    src=Path(src); dst=Path(dst)
    r2=load("patch_psgs_okigraph_r2.py")
    r3=load("patch_psgs_okigraph_r3.py")   # reuse its tree-capable ProDOS D class
    with tempfile.TemporaryDirectory(prefix="psgs_r4_") as td:
        t=Path(td)/"r2.2mg"
        with contextlib.redirect_stdout(io.StringIO()): r2.patch(src,t)
        d=r3.D(t)
        prr=d.find("PRDRIVERS"); mfr=d.find("MF")
        pr=bytearray(d.read(prr)); mf=bytearray(d.read(mfr))
        if sha(pr)!=PR_R2_SHA or sha(mf)!=MF_SHA: raise RuntimeError("R2 baseline mismatch")
        if pr[MAXLF_OFF]!=0x3F: raise RuntimeError("R2 max movement is not $3F")
        if mf[MF_OFF]!=0x10: raise RuntimeError("MF:$75CB is not BCC +$10")
        if mf[0x7608-LOAD]!=0x60: raise RuntimeError("MF:$7608 is not RTS")
        seq=bytes.fromhex("cd 61 78 90 10 f0 0e 48 ad 61 78 20 dc 75 68 38 ed 61 78 80 eb")
        if bytes(mf[0x75C7-LOAD:0x75C7-LOAD+len(seq)])!=seq:
            raise RuntimeError("vertical movement routine mismatch")
        pr[MAXLF_OFF]=0x0E
        mf[MF_OFF]=0x3C
        d.write(prr,bytes(pr)); d.write(mfr,bytes(mf))
        dst.parent.mkdir(parents=True,exist_ok=True); dst.write_bytes(d.r)
    c=r3.D(dst); cp=c.read(c.find("PRDRIVERS")); cm=c.read(c.find("MF"))
    if cp[MAXLF_OFF]!=0x0E or cm[MF_OFF]!=0x3C: raise RuntimeError("post-write verify failed")
    print("output sha  :",sha(dst.read_bytes()))
    print("PRDRIVERS   :",sha(cp))
    print("MF          :",sha(cm))
    print("max movement: $3F -> $0E")
    print("MF:$75CB    : BCC +$10 -> +$3C, suppressing remainders below $0E")

def main():
    a=argparse.ArgumentParser(); a.add_argument("input",type=Path); a.add_argument("output",type=Path)
    x=a.parse_args(); patch(x.input,x.output)
if __name__=="__main__": main()
