#!/usr/bin/env python3
"""Print Shop GS OkiGraph I R2 native graphics-entry patch.

R2 keeps the successful R1 82A/83A + OkiGraph I descriptor behavior but
removes the experimental leading CR from every graphics-entry string.

R1 graphics begin:
    0D 03       CR, ETX

R2 graphics begin:
    03          ETX only

Everything else that worked in R1 is retained:
* selector name: 82A83A OGI
* 7 host-addressable graphics pins
* 60 graphics columns/inch
* PSGS encoder selector 2
* literal raster $03 -> 03 03
* native OkiGraph band movement modeled as 03 03 <n> 03 02
  (for PSGS normal seven-dot band n=$0E: 03 03 0E 03 02)
* graphics exit: 03 02
* stock ML92/93 entry untouched
* no executable code changes

The packed descriptor becomes one logical byte shorter because the graphics
begin string shrinks from two bytes to one. The stock next-descriptor pointer
remains unchanged; the final byte of the original 34-byte ML84 slot becomes
unused zero padding. No descriptor after $0782 moves.

The patch is fail-closed against the known Print Shop GS PRDRIVERS payload.
"""
from __future__ import annotations

import argparse
import hashlib
import struct
from pathlib import Path

BLOCK = 512
ENTRY_LEN = 39
ENTRIES_PER_BLOCK = 13
OLD_NAME = b"Okidata 84"
NEW_NAME = b"82A83A OGI"
EXPECTED_PRDRIVERS_SHA256 = (
    "09e51f041e67fa58756c0c32a362bcff7119488af5070df884f4778fff86e3e0"
)
EXPECTED_NAME_OFFSET = 0x0230
DESC_PTR = 0x0782
NEXT_DESC_PTR = 0x07A4

OLD_DESC = bytes.fromhex(
    "00 "
    "00 00 07 3c 00 48 00 3f 00 "
    "00 "
    "01 0d "
    "03 1b 25 39 81 01 0a "
    "00 00 "
    "01 "
    "02 1e 03 "
    "02 03 02 "
    "03 02 03 03 "
    "02"
)

# R2 semantic descriptor (33 bytes): R1 native movement plus ETX-only begin.
R2_LOGICAL_DESC = bytes.fromhex(
    "00 "
    "00 00 07 3c 00 48 00 3f 00 "
    "00 "
    "01 0d "
    # movement prefix 03 03, raw one-byte n, suffix 03 02
    "02 03 03 81 02 03 02 "
    "00 00 "
    "01 "
    # graphics begin: ETX only
    "01 03 "
    # graphics end: ETX, STX
    "02 03 02 "
    # literal ETX trigger/replacement
    "03 02 03 03 "
    # encoder 2: Oki/7-dot bit transform
    "02"
)

# Preserve the original fixed slot boundary. $07A3 is now padding; the next
# descriptor still begins at the stock pointer $07A4.
R2_SLOT = R2_LOGICAL_DESC + b"\x00"

assert len(OLD_DESC) == 34
assert len(R2_LOGICAL_DESC) == 33
assert len(R2_SLOT) == 34
assert DESC_PTR + len(R2_SLOT) == NEXT_DESC_PTR


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def u16(b: bytes | bytearray | memoryview, o: int) -> int:
    return b[o] | (b[o + 1] << 8)


def u24(b: bytes | bytearray | memoryview, o: int) -> int:
    return b[o] | (b[o + 1] << 8) | (b[o + 2] << 16)


class ProDOS2MG:
    def __init__(self, path: Path):
        self.path = path
        self.raw = bytearray(path.read_bytes())
        if self.raw[:4] != b"2IMG":
            raise RuntimeError("R2 patcher expects a 2IMG/.2mg image")
        self.blocks = struct.unpack_from("<I", self.raw, 20)[0]
        self.data_off = struct.unpack_from("<I", self.raw, 24)[0]
        if not self.blocks:
            raise RuntimeError("2IMG block count is zero")
        if self.data_off + self.blocks * BLOCK > len(self.raw):
            raise RuntimeError("2IMG data range exceeds file size")

    def block(self, n: int) -> memoryview:
        if not 0 <= n < self.blocks:
            raise RuntimeError(f"bad ProDOS block {n}")
        a = self.data_off + n * BLOCK
        return memoryview(self.raw)[a : a + BLOCK]

    def find_root_file(self, wanted: str):
        block = 2
        seen = set()
        while block and block not in seen:
            seen.add(block)
            d = self.block(block)
            nxt = u16(d, 2)
            for i in range(ENTRIES_PER_BLOCK):
                o = 4 + i * ENTRY_LEN
                e = bytes(d[o : o + ENTRY_LEN])
                if len(e) < ENTRY_LEN:
                    continue
                storage = e[0] >> 4
                nlen = e[0] & 0x0F
                if not nlen or storage == 0:
                    continue
                name = e[1 : 1 + nlen].decode("ascii", "replace")
                if name.upper() == wanted.upper():
                    return {
                        "storage": storage,
                        "key": u16(e, 17),
                        "eof": u24(e, 21),
                    }
            block = nxt
        raise RuntimeError(f"{wanted} not found in root directory")

    def sapling_blocks(self, key: int, eof: int) -> list[int]:
        idx = self.block(key)
        need = (eof + BLOCK - 1) // BLOCK
        out = []
        for i in range(need):
            n = idx[i] | (idx[256 + i] << 8)
            if not n:
                raise RuntimeError(f"sparse block {i} in PRDRIVERS")
            out.append(n)
        return out

    def read_file(self, rec) -> bytes:
        if rec["storage"] != 2:
            raise RuntimeError(
                f"PRDRIVERS expected sapling storage=2, got {rec['storage']}"
            )
        blocks = self.sapling_blocks(rec["key"], rec["eof"])
        return b"".join(bytes(self.block(n)) for n in blocks)[: rec["eof"]]

    def write_file_same_size(self, rec, payload: bytes) -> None:
        if len(payload) != rec["eof"]:
            raise RuntimeError("R2 may not change PRDRIVERS length")
        blocks = self.sapling_blocks(rec["key"], rec["eof"])
        for i, n in enumerate(blocks):
            chunk = payload[i * BLOCK : (i + 1) * BLOCK]
            b = self.block(n)
            b[: len(chunk)] = chunk


def parse_record(data: bytes) -> dict:
    p = DESC_PTR
    stride = data[p]; p += 1
    w0 = u16(data, p); p += 2
    pins = data[p]; p += 1
    xdpi = u16(data, p); p += 2
    ydpi = u16(data, p); p += 2
    maxlf = data[p]; p += 1
    colors = data[p]; p += 1

    def getstr(pos: int):
        n = data[pos]
        end = pos + 1 + n
        if end > NEXT_DESC_PTR:
            raise RuntimeError("descriptor string crosses ML84 slot boundary")
        return data[pos + 1 : end], end

    init, p = getstr(p)
    cr, p = getstr(p)
    spacing_prefix, p = getstr(p)
    spacing_spec = data[p]; p += 1
    spacing_suffix, p = getstr(p)
    opt1 = data[p]; p += 1
    opt2 = data[p]; p += 1
    gfxflag = data[p]; p += 1
    gfx_begin, p = getstr(p)
    gfx_end, p = getstr(p)
    trigger = data[p]; p += 1
    replacement, p = getstr(p)
    encoder = data[p]; p += 1
    return {
        "stride": stride, "w0": w0, "pins": pins,
        "xdpi": xdpi, "ydpi": ydpi, "maxlf": maxlf,
        "colors": colors, "init": init, "cr": cr,
        "spacing_prefix": spacing_prefix,
        "spacing_spec": spacing_spec,
        "spacing_suffix": spacing_suffix,
        "opt1": opt1, "opt2": opt2, "gfxflag": gfxflag,
        "gfx_begin": gfx_begin, "gfx_end": gfx_end,
        "trigger": trigger, "replacement": replacement,
        "encoder": encoder, "end": p,
    }


def encode_driver_value(spec: int, value: int) -> bytes:
    mult = spec & 0x0F
    if mult:
        value *= mult
    if not (spec & 0x80):
        raise RuntimeError("R2 expects binary spacing spec $81")
    width = 2 if (spec & 0x30) else 1
    return int(value).to_bytes(width, "little")


def model_band_move(parsed: dict, n: int = 0x0E) -> bytes:
    return (
        parsed["spacing_prefix"]
        + encode_driver_value(parsed["spacing_spec"], n)
        + parsed["spacing_suffix"]
    )


def patch(src: Path, dst: Path) -> None:
    image = ProDOS2MG(src)
    rec = image.find_root_file("PRDRIVERS")
    original = image.read_file(rec)

    if sha256(original) != EXPECTED_PRDRIVERS_SHA256:
        raise RuntimeError("PRDRIVERS baseline mismatch: " + sha256(original))
    if original.find(OLD_NAME) != EXPECTED_NAME_OFFSET or original.count(OLD_NAME) != 1:
        raise RuntimeError("stock Okidata 84 selector does not match baseline")
    after_name = EXPECTED_NAME_OFFSET + len(OLD_NAME)
    if original[after_name : after_name + 4] != bytes.fromhex("00 00 82 07"):
        raise RuntimeError("ML84 selector metadata/pointer does not match baseline")
    if original[DESC_PTR:NEXT_DESC_PTR] != OLD_DESC:
        raise RuntimeError/:ÓÇ!j»-®éÜj×ter[NEXT_DESC_PTR]

    new = parse_record(bytes(patched))
    expected = {
        "pins": 7, "xdpi": 60, "ydpi": 72,
        "spacing_prefix": b"\x03\x03",
        "spacing_spec": 0x81,
        "spacing_suffix": b"\x03\x02",
        "gfx_begin": b"\x03",
        "gfx_end": b"\x03\x02",
        "trigger": 0x03,
        "replacement": b"\x03\x03",
        "encoder": 2,
    }
    for k, v in expected.items():
        if new[k] != v:
            raise RuntimeError(f"R2 parsed field {k} mismatch: {new[k]!r}")

    if new["end"] != NEXT_DESC_PTR - 1:
        raise RuntimeError(
            f"R2 logical descriptor must end at $07A3, got ${new['end']:04X}"
        )
    if patched[NEXT_DESC_PTR - 1] != 0:
        raise RuntimeError("R2 padding byte at $07A3 is not zero")
    if model_band_move(new, 0x0E) != bytes.fromhex("03 03 0e 03 02"):
        raise RuntimeError("R2 $0E band movement changed from native OkiGraph framing")

    # Confirm next stock descriptor was not moved or touched.
    next_before = original[NEXT_DESC_PTR : NEXT_DESC_PTR + 71]
    next_after = patched[NEXT_DESC_PTR : NEXT_DESC_PTR + 71]
    if next_after != next_before:
        raise RuntimeError("R2 modified the descriptor following ML84")

    diffs = [i for i, (a, b) in enumerate(zip(original, patched)) if a != b]
    allowed = set(range(EXPECTED_NAME_OFFSET, EXPECTED_NAME_OFFSET + 10))
    allowed.update(range(DESC_PTR, NEXT_DESC_PTR))
    unexpected = [i for i in diffs if i not in allowed]
    if unexpected:
        raise RuntimeError(f"unexpected PRDRIVERS differences: {unexpected}")

    image.write_file_same_size(rec, bytes(patched))
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(image.raw)

    check = ProDOS2MG(dst)
    check_rec = check.find_root_file("PRDRIVERS")
    check_data = check.read_file(check_rec)
    if check_data != bytes(patched):
        raise RuntimeError("post-write PRDRIVERS verification failed")
    check_parsed = parse_record(check_data)
    if check_parsed != new:
        raise RuntimeError("post-write descriptor parse mismatch")
    if check_data[NEXT_DESC_PTR : NEXT_DESC_PTR + 71] != next_before:
        raise RuntimeError("post-write next descriptor mismatch")

    before_disk = src.read_bytes()
    after_disk = dst.read_bytes()
    disk_diffs = [i for i, (a, b) in enumerate(zip(before_disk, after_disk)) if a != b]
    if len(before_disk) != len(after_disk) or len(disk_diffs) != len(diffs):
        raise RuntimeError(
            f"disk changed outside PRDRIVERS patch: disk={len(disk_diffs)} file={len(diffs)}"
        )

    print(f"source disk : {src}")
    print(f"source sha  : {sha256(before_disk)}")
    print(f"output disk : {dst}")
    print(f"output sha  : {sha256(after_disk)}")
    print(f"PRDRIVERS   : {sha256(original)} -> {sha256(check_data)}")
    print(f"selector    : {OLD_NAME.decode()} -> {NEW_NAME.decode()}")
    print(f"descriptor  : ${DESC_PTR:04X} native OkiGraph-I R2")
    print("gfx begin   : 03          (ETX only)")
    print("band move   : 03 03 <n> 03 02; expected raster n=0E")
    print("gfx end     : 03 02")
    print("ETX escape  : 03 -> 03 03")
    print("encoder     : 2 (existing Oki/7-dot transform)")
    print(f"logical end : ${new['end']:04X}; pad at ${NEXT_DESC_PTR - 1:04X}")
    print(f"disk diffs  : {len(disk_diffs)} bytes")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()
    patch(args.input, args.output)


if __name__ == "__main__":
    main()
