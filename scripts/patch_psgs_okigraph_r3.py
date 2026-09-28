#!/usr/bin/env python3
"""Print Shop GS OkiGraph I R3 horizontal-scaler row-reset patch.

R3 keeps the R2 native 82A/83A + OkiGraph I descriptor unchanged and patches
one three-byte instruction in MF so every raster row explicitly resets PSGS's
60-dpi horizontal reducer before any leading blank columns or real raster data
are emitted.

Code trace:
  $72F3  row setup
    STA $7303
    STX $7305
    STZ $7307        ; dead state word: no read references in MF
    STZ $7309
    STZ $730B
    RTS

R3 changes only:
    $72F9: STZ $7307  (9C 07 73)
        -> JSR $7525  (20 25 75)

$7525 is an existing PSGS helper tail which does:
    STZ $73E7        ; horizontal reducer phase index
    STZ $7869        ; first OR accumulator
    STZ $786B        ; second OR accumulator
    RTS

This is intentionally not a protocol change. R2 descriptor semantics remain:
  graphics begin:        03
  literal raster $03:    03 03
  band movement:         03 03 <n> 03 02  (n=$0E normally)
  graphics end:          03 02
  encoder:               2 (existing Oki/7-dot transform)

The R3 patcher depends on patch_psgs_okigraph_r2.py in the same directory so
R2's fail-closed descriptor validation remains the single source of truth.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import io
import struct
import tempfile
from pathlib import Path

BLOCK = 512
ENTRY_LEN = 39
ENTRIES_PER_BLOCK = 13
MF_SHA256 = "12b35bc7e4bfa08268399a2b8ef65750230ff8625f72302106677594977ff7e3"
MF_LOAD = 0x0800
ROW_SETUP_ADDR = 0x72F9
ROW_SETUP_OFF = ROW_SETUP_ADDR - MF_LOAD
OLD_MF_BYTES = bytes.fromhex("9c 07 73")
NEW_MF_BYTES = bytes.fromhex("20 25 75")
RESET_HELPER_ADDR = 0x7525
RESET_HELPER_OFF = RESET_HELPER_ADDR - MF_LOAD
RESET_HELPER_BYTES = bytes.fromhex("9c e7 73 9c 69 78 9c 6b 78 60")
EXPECTED_R2_PRDRIVERS_SHA256 = "fbfed119fcfb2cfcc4d37e2d20453c3b561f7a91faac01be34c1bf4b840112b1"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def u16(b, o: int) -> int:
    return b[o] | (b[o + 1] << 8)


def u24(b, o: int) -> int:
    return b[o] | (b[o + 1] << 8) | (b[o + 2] << 16)


class ProDOS2MG:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.raw = bytearray(self.path.read_bytes())
        if self.raw[:4] != b"2IMG":
            raise RuntimeError("R3 patcher expects a 2IMG/.2mg image")
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
        return memoryview(self.raw)[a:a + BLOCK]

    def find_root_file(self, wanted: str):
        block = 2
        seen = set()
        while block and block not in seen:
            seen.add(block)
            d = self.block(block)
            nxt = u16(d, 2)
            for i in range(ENTRIES_PER_BLOCK):
                o = 4 + i * ENTRY_LEN
                e = bytes(d[o:o + ENTRY_LEN])
                if len(e) < ENTRY_LEN:
                    continue
                storage = e[0] >> 4
                nlen = e[0] & 0x0F
                if not nlen or storage == 0:
                    continue
                name = e[1:1 + nlen].decode("ascii", "replace")
                if name.upper() == wanted.upper():
                    return {
                        "storage": storage,
                        "key": u16(e, 17),
                        "eof": u24(e, 21),
                    }
            block = nxt
        raise RuntimeError(f"{wanted} not found in root directory")

    def data_blocks(self, rec) -> list[int]:
        st, key, eof = rec["storage"], rec["key"], rec["eof"]
        need = (eof + BLOCK - 1) // BLOCK
        if st == 1:
            if need != 1:
                raise RuntimeError("seedling file spans more than one block")
            return [key]
        if st == 2:
            idx = self.block(key)
            out = []
            for i in range(need):
                n = idx[i] | (idx[256 + i] << 8)
                if not n:
                    raise RuntimeError("sparse sapling file")
                out.append(n)
            return out
        if st == 3:
            master = self.block(key)
            out = []
            sapneed = (need + 255) // 256
            for si in range(sapneed):
                sk = master[si] | (master[256 + si] << 8)
                if not sk:
                    raise RuntimeError.úÙÈZ®Ëkºwµçut
            out = []
            sapneed = (need + 255) // 256
            for si in range(sapneed):
                sk = master[si] | (master[256 + si] << 8)
                if not sk:
                    raise RuntimeError.úÙÈZ®Ëkºwµç][H[ŠÝ]
JBˆ›ÜˆH[ˆ˜[™ÙJÛÝ[
N‚ˆˆHYÚWH
YÌMˆ
ÈWH
BˆYˆ›Ýˆ‚ˆ˜Z\ÙH[[YQ\œ›Üˆ ‰ÍÁ…ÉÍ”ÑÉ•”‘…Ñ„ˆ¤(€€€€€€€€€€€€€€€€€€€½ÕÐ¹…ÁÁ•¹¡¸¤(€€€€€€€€€€€É•ÑÕÉ¸½ÕÐ(€€€€€€€É…¥Í”IÕ¹Ñ¥µ•ÉÉ½È¡˜‰Õ¹ÍÕÁÁ½ÉÑ•AÉ½=LÍÑ½É…”ÑåÁ”íÍÑôˆ¤((€€€‘•˜É•…‘}™¥±”¡Í•±˜°É•Œ¤€´ø‰åÑ•Ìè(€€€€€€€É•ÑÕÉ¸ˆˆˆ¹©½¥¸¡‰åÑ•Ì¡Í•±˜¹‰±½¬¡¸¤¤™½È¸¥¸Í•±˜¹‘…Ñ…}‰±½­Ì¡É•Œ¤¥léÉ•l‰•½˜‰ut((€€€‘•˜ÝÉ¥Ñ•}™¥±•}Í…µ•}Í¥é”¡Í•±˜°É•Œ°Á…å±½…è‰åÑ•Ì¤€´ø9½¹”è(€€€€€€€¥˜±•¸¡Á…å±½…¤€„ôÉ•l‰•½˜‰tè(€€€€€€€€€€€É…¥Í”IÕ¹Ñ¥µ•ÉÉ½È ‰HÌµ…ä¹½Ð¡…¹”™¥±”±•¹Ñ ˆ¤(€€€€€€€™½È¤°¸¥¸•¹Õµ•É…Ñ”¡Í•±˜¹‘…Ñ…}‰±½­Ì¡É•Œ¤¤è(€€€€€€€€€€€¡Õ¹¬€ôÁ…å±½…‘m¤€¨	1=,è¡¤€¬€Ä¤€¨	1=-t(€€€€€€€€€€€‰±¬€ôÍ•±˜¹‰±½¬¡¸¤(€€€€€€€€€€€‰±­lé±•¸¡¡Õ¹¬¥t€ô¡Õ¹¬(()‘•˜±½…‘}ÈÉ}µ½‘Õ±” ¤è(€€€¡•É”€ôA…Ñ ¡}}™¥±•}|¤¹É•Í½±Ù” ¤¹Á…É•¹Ð(€€€À€ô¡•É”€¼€‰Á…Ñ¡}ÁÍÍ}½­¥É…Á¡}ÈÈ¹Áäˆ(€€€¥˜¹½ÐÀ¹•á¥ÍÑÌ ¤è(€€€€€€€É…¥Í”IÕ¹Ñ¥µ•ÉÉ½È¡˜‰É•ÅÕ¥É•Í¥‰±¥¹œHÈÁ…Ñ¡•È¹½Ð™½Õ¹èíÁôˆ¤(€€€ÍÁ•Œ€ô¥µÁ½ÉÑ±¥ˆ¹ÕÑ¥°¹ÍÁ•}™É½µ}™¥±•}±½…Ñ¥½¸ ‰ÁÍÍ}ÈÈˆ°À¤(€€€¥˜ÍÁ•Œ¥Ì9½¹”½ÈÍÁ•Œ¹±½…‘•È¥Ì9½¹”è(€€€€€€€É…¥Í”IÕ¹Ñ¥µ•ÉÉ½ÈŠ˜Ø[››ÝØYŒˆ]Ú\ˆŠBˆ[ÙH[\ÜX‹][›[Ù[WÙœ›ÛWÜÜXÊÜXÊBˆÜXË›ØY\‹™^X×Û[Ù[J[Ù
Bˆ™]\›ˆ[Ù‚‚™Yˆ]Ú
Ü˜Îˆ]Ýˆ]
HOˆ›Û™N‚ˆÜ˜ÈH]
Ü˜ÊBˆÝH]
Ý
BˆŒˆHØYÜŒ—Û[Ù[J
B‚ˆÚ][\š[K•[\Ü˜\žQ\™XÝÜžJ™Yš^HœÙÜ×ÜŒ×ÈŠH\È‚ˆŒ\H]

HÈœŒ‹Œ›YÈ‚ˆÈÙY\ŒÉÜÈÛÛœÛÛHÝ]]›ØÝ\ÙYÈŒˆÝ[\™›Ü›\È[Ùˆ]ÂˆÈ˜Z[XÛÜÙY˜[Y][ÛœÈ[\›˜[K‚ˆÚ]ÛÛ^X‹œ™Y\™XÝÜÝÝ]
[Ë”Ýš[™ÒSÊ
JN‚ˆŒ‹œ]Ú
Ü˜ËŒ\
B‚ˆ[XYÙHH›ÑÔÌ“QÊŒ\
BˆˆH[XYÙK™š[™Ü›ÛÝÙš[J”‘’U‘T”ÈŠBˆ™]HH[XYÙKœ™XYÙš[JŠBˆYˆÚLMŠ™]JHOHVPÕQÔŒ—Ô‘’U‘T”×ÔÒLMŽ‚ˆ˜Z\ÙH[[YQ\œ›ÜŠ”Œˆ‘’U‘T”È˜\Ù[[™HZ\ÛX]Ú[œÚYHŒÈŠB‚ˆYœ™XÈH[XYÙK™š[™Ü›ÛÝÙš[J“QˆŠBˆYˆH[XYÙKœ™XYÙš[JYœ™XÊBˆYˆÚLMŠYŠHOHQ—ÔÒLMŽ‚ˆ˜Z\ÙH[[YQ\œ›ÜŠ“Qˆ˜\Ù[[™HZ\ÛX]Úˆˆ
ÈÚLMŠYŠJBˆYˆY–Ô“Õ×ÔÑUTÓÑ‘Ž”“Õ×ÔÑUTÓÑ‘ˆ
È×HOHÓÓQ—Ð–UTÎ‚ˆ˜Z\ÙH[[YQ\œ›Üˆ ‰Qˆ›ÝË\Ù]\ž]\È]	Ì‘ŽHÈ›ÝX]Ú˜\Ù[[™HŠBˆYˆY–Ô‘TÑUÒST—ÓÑ‘Ž”‘TÑUÒST—ÓÑ‘ˆ
È[Š‘TÑUÒST—Ð–UTÊWHOH‘TÑUÒST—Ð–UTÎ‚ˆ˜Z\ÙH[[YQ\œ›Üˆ ‰Qˆ™\Ù][\ˆ]	ÍLHÙ\È›ÝX]Ú˜\Ù[[™HŠB‚ˆ]ÚYÛYˆHž]X\œ˜^JYŠBˆ]ÚYÛY–Ô“Õ×ÔÑUTÓÑ‘Ž”“Õ×ÔÑUTÓÑ‘ˆ
È×HH‘U×ÓQ—Ð–UTÂˆY—ÙY™œÈHÚH›ÜˆK
KŠH[ˆ[[Y\˜]Jš\
Y‹]ÚYÛYŠJHYˆHOH—BˆYˆY—ÙY™œÈOHÔ“Õ×ÔÑUTÓÑ‘‹“Õ×ÔÑUTÓÑ‘ˆ
ÈK“Õ×ÔÑUTÓÑ‘ˆ
È—N‚ˆ˜Z\ÙH[[YQ\œ›ÜŠˆ[™^XÝYQˆY™™\™[˜Ù\ÎˆÛY—ÙY™œßHŠB‚ˆ[XYÙKÜš]WÙš[WÜØ[YWÜÚ^™JYœ™XËž]\Ê]ÚYÛYŠJBˆÝœ\™[›ZÙ\Š\™[ÏUYK^\ÝÛÚÏUYJBˆÝÜš]WØž]\Ê[XYÙKœ˜]ÊB‚ˆÈ™[Ü[ˆš[˜[[XYÙH[™™\šYžH›Ý]ÚYš[\Ë‚ˆÚXÚÈH›ÑÔÌ“QÊÝ
BˆÛYœ™XÈHÚXÚË™š[™Ü›ÛÝÙš[J“QˆŠBˆÛYˆHÚXÚËœ™XYÙš[JÛYœ™XÊBˆÜˆHÚXÚËœ™XYÙš[JÚXÚË™š[™Ü›ÛÝÙš[J”‘’U‘T”ÈŠJBˆYˆÛYˆOHž]\Ê]ÚYÛYŠN‚ˆ˜Z\ÙH[[YQ\œ›ÜŠœÜÝ]Üš]HQˆ™\šYšXØ][Ûˆ˜Z[YŠBˆYˆÚLMŠÜŠHOHVPÕQÔŒ—Ô‘’U‘T”×ÔÒLMŽ‚ˆ˜Z\ÙH[[YQ\œ›ÜŠœÜÝ]Üš]H‘’U‘T”È™\šYšXØ][Ûˆ˜Z[YŠBˆYˆÛY–Ô“Õ×ÔÑUTÓÑ‘Ž”“Õ×ÔÑUTÓÑ‘ˆ
È×HOH‘U×ÓQ—Ð–UTÎ‚ˆ˜Z\ÙH[[YQ\œ›ÜŠœÜÝ]Üš]H›ÝË\™\Ù]ÛÚÈ™\šYšXØ][Ûˆ˜Z[YŠB‚ˆ™Y›Ü™HHÜ˜Ëœ™XYØž]\Ê
BˆY\ˆHÝœ™XYØž]\Ê
BˆYˆ[Š™Y›Ü™JHOH[ŠY\ŠN‚ˆ˜Z\ÙH[[YQ\œ›Üˆ ‰HÈÕ¹•áÁ•Ñ•‘±ä¡…¹•‘¥Í¬¥µ…”Í¥é”ˆ¤(€€€‘¥Í­}‘¥™™Ì€ôm¤™½È¤°€¡„°ˆ¤¥¸•¹Õµ•É…Ñ”¡é¥À¡‰•™½É”°…™Ñ•È¤¤¥˜„€„ô‰t((€€€ÁÉ¥¹Ð¡˜‰Í½ÕÉ”‘¥Í¬€èíÍÉôˆ¤(€€€ÁÉ¥¹Ð¡˜‰Í½ÕÉ”Í¡„€€èíÍ¡„ÈÔØ¡‰•™½É”¥ôˆ¤(€€€ÁÉ¥¹Ð¡˜‰½ÕÑÁÕÐ‘¥Í¬€èí‘ÍÑôˆ¤(€€€ÁÉ¥¹Ð¡˜‰½ÕÑÁÕÐÍ¡„€€èíÍ¡„ÈÔØ¡…™Ñ•È¥ôˆ¤(€€€ÁÉ¥¹Ð¡˜‰AII%YIL€€€èíÍ¡„ÈÔØ¡ÁÈ¥ô€¡HÈ¹…Ñ¥Ù”‘•ÍÉ¥ÁÑ½ÈÕ¹¡…¹•¤ˆ¤(€€€ÁÉ¥¹Ð¡˜‰5€€€€€€€€€€èí5}M!ÈÔÙô€´øíÍ¡„ÈÔØ¡µ˜¥ôˆ¤(€€€ÁÉ¥¹Ð ‰É½ÜÍ•ÑÕÀ€€€è€ÜÉäMQh€ÜÌÀÜ€´ø)MH€ÜÔÈÔˆ¤(€€€ÁÉ¥¹Ð ‰É•Í•Ð¡•±Á•Èè€ÜÔÈÔ±•…ÉÌ€ÜÍÜ¼ÜàØä¼ÜàÙˆ¤(€€€ÁÉ¥¹Ð ‰ÁÉ½Ñ½½°€€€€è¥‘•¹Ñ¥…°Ñ¼HÈˆ¤(€€€ÁÉ¥¹Ð¡˜‰‘¥Í¬‘¥™™Ì€€èí±•¸¡‘¥Í­}‘¥™™Ì¥ô‰åÑ•ÌÙ•ÉÍÕÌ½É¥¥¹…°ˆ¤(()‘•˜µ…¥¸ ¤è(€€€…À€ô…ÉÁ…ÉÍ”¹ÉÕµ•¹ÑA…ÉÍ•È ¤(€€€…À¹…‘‘}…ÉÕµ•¹Ð ‰¥¹ÁÕÐˆ°ÑåÁ”õA…Ñ ¤(€€€…À¹…‘‘}…ÉÕµ•¹Ð ‰½ÕÑÁÕÐˆ°ÑåÁ”õA…Ñ ¤(€€€…ÉÌ€ô…À¹Á…ÉÍ•}…ÉÌ ¤(€€€Á…Ñ ¡…ÉÌ¹¥¹ÁÕÐ°…ÉÌ¹½ÕÑÁÕÐ¤(()¥˜}}¹…µ•}|€ôô€‰}}µ…¥¹}|ˆè(€€€µ…¥¸ ¤(