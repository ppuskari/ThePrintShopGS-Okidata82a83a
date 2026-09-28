#!/usr/bin/env python3
"""Print Shop GS OkiGraph I R5 native movement sanitizer.

R5 starts from the hardware-coherent R2 descriptor and fixes the remaining
unsafe generic vertical-movement behavior without carrying R3 or R4 forward.

R2's native movement descriptor is valid only when the dynamic value is $0E:
    03 03 0E 03 02
which, from text state, is:
    03       enter graphics
    03 0E    native OkiGraph graphics LF + CR
    03 02    exit graphics

The PSGS generic movement routine can request smaller/larger values. R5 sets
this driver's max movement chunk to $0E and replaces MF:$75C7's CMP with a
call to a tiny compare hook in existing zero padding at $7E67. The hook is
active only when max movement == $0E. For positive sub-$0E remainders it
rounds the value up to $0E; otherwise it preserves the stock comparison.
The original MF chunk loop therefore emits ceil(distance/14) proven native
OkiGraph feeds and never places an arbitrary value after ETX.

The high-level PSGS path gates zero movement before calling the printer
vertical routine, so this hook is only expected to receive positive distances
for the OkiGraph path.

Other printer descriptors keep their original max-movement value, so the hook
falls through to the stock CMP semantics for them.
"""
from pathlib import Path
import argparse, contextlib, hashlib, importlib.util, io, tempfile

LOAD = 0x0800
MF_SHA = "12b35bc7e4bfa08268399a2b8ef65750230ff8625f72302106677594977ff7e3"
PR_R2_SHA = "fbfed119fcfb2cfcc4d37e2d20453c3b561f7a91faac01be34c1bf4b840112b1"

DESC_PTR = 0x0782
MAXLF_OFF = DESC_PTR + 8
VERT_CMP_ADDR = 0x75C7
VERT_CMP_OFF = VERT_CMP_ADDR - LOAD
CAVE_ADDR = 0x7E67
CAVE_OFF = CAVE_ADDR - LOAD
CAVE_LIMIT = 0x7E8D
CAVE_LEN = CAVE_LIMIT - CAVE_ADDR

OLD_CMP = bytes.fromhex("cd 61 78")       # CMP $7861
NEW_CMP = bytes.fromhex("20 67 7e")       # JSR $7E67

# $7E67 compare hook, 27 bytes.
#
#   PHA
#   LDX $7861
#   CPX #$000E
#   BNE normal
#   PLA
#   CMP #$000E
#   BCS compare
#   LDA #$000E
# compare:
#   CMP $7861
#   RTS
# normal:
#   PLA
#   CMP $7861
#   RTS
#
# Caller resumes at MF:$75CA with the stock BCC/BEQ/chunk loop.
HOOK = bytes.fromhex(
    "48 "              # PHA
    "ae 61 78 "        # LDX $7861
    "e0 0e 00 "        # CPX #$000E
    "d0 0d "           # BNE normal
    "68 "              # PLA
    "c9 0e 00 "        # CMP #$000E
    "b0 03 "           # BCS compare
    "a9 0e 00 "        # LDA #$000E
    "cd 61 78 "        # compare: CMP $7861
    "60 "              # RTS
    "68 "              # normal: PLA
    "cd 61 78 "        # CMP $7861
    "60"               # RTS
)
assert len(HOOK) == 27
assert len(HOOK) <= CAVE_LEN


def sha(x: bytes) -> str:
    return hashlib.sha256(x).hexdigest()


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if not path.exists() or spec is None or spec.loader is None:
        raise RuntimeError(f"required helper missing: {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def patch(src: Path, dst: Path) -> None:
    src = Path(src)
    dst = Path(dst)
    here = Path(__file__).resolve().parent
    r2 = load_module(here / "patch_psgs_okigraph_r2.py", "psgs_r2")
    r3 = load_module(here / "patch_psgs_okigraph_r3.py", "psgs_r3_helper")

    with tempfile.TemporaryDirectory(prefix="psgs_r5_") as td:
        r2tmp = Path(td) / "r2.2mg"
        with contextlib.redirect_stdout(io.StringIO()):
            r2.patch(src, r2tmp)

        image = r3.D(r2tmp)
        prrec = image.find("PRDRIVERS")
        mfrec = image.find("MF")
        pr = bytearray(image.read(prrec))
        mf = bytearray(image.read(mfrec))

        if sha(pr) != PR_R2_SHA:
            raise RuntimeError("R2 PRDRIVERS baseline mismatch: " + sha(pr))
        if sha(mf) != MF_SHA:
            raise RuntimeError("MF baseline mismatch: " + sha(mf))
        if pr[MAXLF_OFF] != 0x3F:
            raise RuntimeError("R2 OkiGraph max movement is not $3F")
        if mf[VERT_CMP_OFF:VERT_CMP_OFF + 3] != OLD_CMP:
            raise RuntimeError("MF:$75C7 is not CMP $7861")
        if any(mf[CAVE_OFF:CAVE_OFF + CAVE_LEN]):
            raise RuntimeError("MF $7E67-$7E8C padding is not all zero")
        # Keep R4's failed BCC experiment out of R5.
        if mf[0x75CA - LOAD:0x75CC - LOAD] != bytes.fromhex("90 10"):
            raise RuntimeError("MF:$75CA stock BCC +$10 not present")
        # High-level movement gate: nonzero pending movement before JSR $73CC.
        gate = bytes.fromhex("ad ce 72 f0 06 20 cc 73 9c ce 72 60")
        goff = 0x72E7 - LOAD
        if mf[goff:goff + len(gate)] != gate:
            raise RuntimeError("expected nonzero vertical-movement gate not present")

        pr[MAXLF_OFF] = 0x0E
        mf[VERT_CMP_OFF:VERT_CMP_OFF + 3] = NEW_CMP
        mf[CAVE_OFF:CAVE_OFF + len(HOOK)] = HOOK

        # Structural validation before write.
        if pr[MAXLF_OFF] != 0x0E:
            raise RuntimeError("R5 max movement patch failed")
        if mf[VERT_CMP_OFF:VERT_CMP_OFF + 3] != NEW_CMP:
            raise RuntimeError("R5 compare-hook patch failed")
        if mf[CAVE_OFF:CAVE_OFF + len(HOOK)] != HOOK:
            raise RuntimeError("R5 code-cave patch failed")
        if any(mf[CAVE_OFF + len(HOOK):CAVE_OFF + CAVE_LEN]):
            raise RuntimeError("R5 modified padding beyond hook")

        image.write(prrec, bytes(pr))
        image.write(mfrec, bytes(mf))
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(image.r)

    # Reopen and verify filesystem payloads.
    check = r3.D(dst)
    cpr = check.read(check.find("PRDRIVERS"))
    cmf = check.read(check.find("MF"))
    if cpr != bytes(pr) or cmf != bytes(mf):
        raise RuntimeError("post-write ProDOS verification failed")

    before = src.read_bytes()
    after = dst.read_bytes()
    if len(before) != len(after):
        raise RuntimeError("disk image size changed")

    # R2 has 27 PRDRIVERS-byte diffs vs original. R5 adds one descriptor-byte
    # change plus 30 MF bytes (3-byte hook call + 27-byte cave), but overlap in
    # physical bytes is checked by direct accounting below rather than assumed.
    disk_diffs = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]

    print(f"source disk   : {src}")
    print(f"source sha    : {sha(before)}")
    print(f"output disk   : {dst}")
    print(f"output sha    : {sha(after)}")
    print(f"PRDRIVERS     : {sha(cpr)}")
    print(f"MF            : {sha(cmf)}")
    print("max movement  : $3F -> $0E (R5 marker/chunk)")
    print("MF:$75C7      : CMP $7861 -> JSR $7E67")
    print("MF:$7E67 hook : sub-$0E positive Oki values -> $0E; stock compare otherwise")
    print("MF:$75CA      : remains stock BCC +$10")
    print(f"disk diffs    : {len(disk_diffs)} bytes vs original")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()
    patch(args.input, args.output)


if __name__ == "__main__":
    main()
