#!/usr/bin/env python3
"""Print Shop GS OkiGraph I R0 proof patch.

Repurposes the existing 10-character "Okidata 84" selector as
"82A83A OGI" while leaving its PRDRIVERS descriptor at $0782 byte-for-byte
unchanged.  This deliberately tests whether Broderbund's ML84 descriptor is
already wire-compatible with MICROLINE 82A/83A + OkiGraph I.

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
OLD = b"Okidata 84"
NEW = b"82A83A OGI"
EXPECTED_PRDRIVERS_SHA256 = (
    "09e51f041e67fa58756c0c32a362bcff7119488af5070df884f4778fff86e3e0"
)
EXPECTED_NAME_OFFSET = 0x0230
EXPECTED_DESCRIPTOR_PTR = 0x0782
EXPECTED_DESCRIPTOR = bytes.fromhex(
    "00 00 00 07 3c 00 48 00 3f 00 00 01 0d 03 1b 25 "
    "39 81 01 0a 00 00 01 02 1e 03 02 03 02 03 02 03 "
    "03 02"
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def u16(b: bytes | bytearray, o: int) -> int:
    return b[o] | (b[o + 1] << 8)


def u24(b: bytes | bytearray, o: int) -> int:
    return b[o] | (b[o + 1] << 8) | (b[o + 2] << 16)


class ProDOS2MG:
    def __init__(self, path: Path):
        self.path = path
        self.raw = bytearray(path.read_bytes())
        if self.raw[:4] != b"2IMG":
            raise RuntimeError("R0 patcher expects a 2IMG/.2mg image")
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
                        "dir_block": block,
                        "dir_index": i,
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
            raise RuntimeError("R0 may not change PRDRIVERS length")
        blocks = self.sapling_blocks(rec["key"], rec["eof"])
        for i, n in enumerate(blocks):
            chunk = payload[i * BLOCK : (i + 1) * BLOCK]
            b = self.block(n)
            b[: len(chunk)] = chunk


def patch(src: Path, dst: Path) -> None:
    image = ProDOS2MG(src)
    rec = image.find_root_file("PRDRIVERS")
    original = image.read_file(rec)

    if sha256(original) != EXPECTED_PRDRIVERS_SHA256:
        raise RuntimeError(
            "PRDRIVERS baseline mismatch: " + sha256(original)
        )
    if original.find(OLD) != EXPECTED_NAME_OFFSET:
        raise RuntimeError("Okidata 84 selector not at expected $0230")
    if original.count(OLD) != 1:
        raise RuntimeError("Okidata 84 selector is not unique")

    after_name = EXPECTED_NAME_OFFSET + len(OLD)
    if original[after_name : after_name + 4] != bytes.fromhex("00 00 82 07"):
        raise RuntimeError("ML84 entry metadata/pointer does not match baseline")
    if original[EXPECTED_DESCRIPTOR_PTR : EXPECTED_DESCRIPTOR_PTR + len(EXPECTED_DESCRIPTOR)] != EXPECTED_DESCRIPTOR:
        raise RuntimeError("ML84 descriptor does not match baseline")

    patched = bytearray(original)
    patched[EXPECTED_NAME_OFFSET : EXPECTED_NAME_OFFSET + len(OLD)] = NEW

    diffs = [i for i, (a, b) in enumerate(zip(original, patched)) if a != b]
    expected_diffs = [
        EXPECTED_NAME_OFFSET + i
        for i, (a, b) in enumerate(zip(OLD, NEW))
        if a != b
    ]
    if diffs != expected_diffs:
        raise RuntimeError(f"unexpected PRDRIVERS differences: {diffs}")
    if patched[EXPECTED_DESCRIPTOR_PTR : EXPECTED_DESCRIPTOR_PTR + len(EXPECTED_DESCRIPTOR)] != EXPECTED_DESCRIPTOR:
        raise RuntimeError("R0 unexpectedly changed ML84 descriptor")

    image.write_file_same_size(rec, bytes(patched))
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(image.raw)

    # Re-open and verify from the resulting disk image.
    check = ProDOS2MG(dst)
    check_rec = check.find_root_file("PRDRIVERS")
    check_data = check.read_file(check_rec)
    if check_data != bytes(patched):
        raise RuntimeError("post-write PRDRIVERS verification failed")
    if check_data[EXPECTED_NAME_OFFSET : EXPECTED_NAME_OFFSET + 10] != NEW:
        raise RuntimeError("post-write selector verification failed")
    ptr = u16(check_data, EXPECTED_NAME_OFFSET + 12)
    if ptr != EXPECTED_DESCRIPTOR_PTR:
        raise RuntimeError(f"post-write descriptor pointer changed to ${ptr:04X}")

    before_disk = src.read_bytes()
    after_disk = dst.read_bytes()
    disk_diffs = [i for i, (a, b) in enumerate(zip(before_disk, after_disk)) if a != b]
    if len(before_disk) != len(after_disk) or len(disk_diffs) != len(expected_diffs):
        raise RuntimeError(
            f"disk changed outside expected selector bytes: {len(disk_diffs)} diffs"
        )

    print(f"source disk : {src}")
    print(f"source sha  : {sha256(before_disk)}")
    print(f"output disk : {dst}")
    print(f"output sha  : {sha256(after_disk)}")
    print(f"PRDRIVERS   : {sha256(original)} -> {sha256(check_data)}")
    print(f"selector    : {OLD.decode()} -> {NEW.decode()}")
    print(f"name offset : ${EXPECTED_NAME_OFFSET:04X}")
    print(f"descriptor  : ${EXPECTED_DESCRIPTOR_PTR:04X} (UNCHANGED)")
    print(f"disk diffs  : {len(disk_diffs)} bytes")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()
    patch(args.input, args.output)


if __name__ == "__main__":
    main()
