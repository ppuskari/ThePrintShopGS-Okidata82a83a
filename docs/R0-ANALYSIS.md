# Print Shop GS — Okidata 82A/83A OkiGraph I — R0

## Purpose

R0 is intentionally the smallest possible hardware proof. It repurposes the
existing **Okidata 84** printer selector as **82A83A OGI**, but leaves the
ML84 printer descriptor at `PRDRIVERS+$0782` byte-for-byte unchanged.

This isolates the first question:

> Is Print Shop GS's existing ML84/Oki graphics descriptor already compatible
> enough with the 82A/83A OkiGraph I firmware to render recognizable output?

No other printer entry, descriptor, interface driver, executable, or disk file
is altered.

## Print Shop GS driver architecture found so far

`PRDRIVERS` is 2565 bytes and starts with 46 printer-name records. Each record
is:

```
ASCII name, $00, color-capability byte, descriptor pointer (16-bit LE)
```

The name table ends at `$0380`. The descriptor pool starts immediately after.

The relevant original entry is:

```
name:       Okidata 84
color:      $00
pointer:    $0782
```

SETMAKE's printer entry at `$9800` does not compile this descriptor. It patches
an inline 24-bit source pointer and invokes the application's block-copy helper
to copy exactly `$0080` bytes from the selected `PRDRIVERS` descriptor to the
live printer-driver workspace. The separate SETMAKE entry at `$9803` is the
compiler for the selected *interface* descriptor from `INTDRIVERS`.

Therefore an in-place PRDRIVERS experiment is clean and bounded.

## ML84 descriptor

Descriptor begins at `PRDRIVERS+$0782`:

```
0782: 00
0783: 00 00 07 3C 00 48 00 3F 00 00
078D: 01 0D
078F: 03 1B 25 39
0793: 81
0794: 01 0A
0796: 00 00
0798: 01
0799: 02 1E 03
079C: 02 03 02
079F: 03 02 03 03
07A3: 02
```

Current interpretation, with confidence levels:

| Bytes | Interpretation | Confidence |
|---|---|---|
| `$0782 = 00` | one-quality/single-record descriptor rather than Normal+Draft stride | high |
| record byte 2 = `07` | seven-dot graphics packing/head depth | high |
| record bytes 3-4 = `003C` | 60 horizontal graphics columns/inch | high |
| record bytes 5-6 = `0048` | 72 logical vertical dots/inch | high |
| `01 0D` | one-byte CR string (`$0D`) | high |
| `03 1B 25 39` | three-byte line-spacing prefix `ESC % 9` | high |
| `81` | spacing-parameter scaling/encoding selector; likely converts PSGS logical spacing to n/144 units | medium-high |
| `01 0A` | one-byte LF string (`$0A`) | high |
| `02 1E 03` | two-byte graphics entry string: `RS, ETX` (10 CPI/60-dpi selection then Oki graphics state) | high |
| `02 03 02` | two-byte Oki graphics exit string `ETX, STX` | high |
| `03 02 03 03` | strongly consistent with an ETX graphics-data escape definition using doubled `ETX,ETX` for literal `$03` | medium-high |
| final `02` | Oki/7-dot graphics packing/encoder selector | medium |

The exact meanings of the remaining zero/flag bytes are still being traced.
They are deliberately untouched in R0.

## Why the unchanged ML84 descriptor is a strong first candidate

The ML84 descriptor already selects:

- 7-dot graphics handling;
- 60 horizontal graphics columns/inch;
- Oki `ESC % 9` programmable line spacing;
- `RS` / 10-CPI selection before graphics;
- ETX graphics mode;
- ETX-STX graphics exit; and
- an Oki-specific tail consistent with doubled ETX handling for literal `$03`
  graphics data.

Those are the same protocol family characteristics recovered independently
from the 82A/83A OkiGraph I firmware.

## Known expected mismatch: vertical mechanics

This is the important R0 caveat.

The standard Oki Microline 7-bit graphics model is based on a graphics band
advance of:

```
14/144 inch = 7/72 inch
```

The physically validated 82A/83A OkiGraph I firmware advances:

```
15/144 inch
```

The ratio is:

```
(15/144) / (14/144) = 15/14 = 1.071428...
```

So if PSGS's ML84 renderer assumes the standard 14/144 band origin advance,
R0 output on OkiGraph I should be recognizable and horizontally correct but
may be approximately **7.14% too tall** over long vertical spans, with a small
extra inter-band spacing.

That is useful diagnostic behavior, not an R0 failure.

If R0 otherwise prints correctly, R1 should target vertical geometry only.
The first low-risk experiment would be the descriptor's logical Y-resolution
field (`$0048 = 72`) rather than altering the already-correct Oki control
framing. A value near 67 dpi is the obvious experiment because seven exposed
dots per 15/144-inch native band gives an average 67.2 dot rows/inch. Exact
high-quality correction may still require nonuniform band-aware resampling,
as the Linux/CUPS work demonstrated.

## R0 disk modification

Original PRDRIVERS selector at `$0230`:

```
Okidata 84
```

R0 selector:

```
82A83A OGI
```

Both strings are exactly 10 bytes. The following bytes remain:

```
00 00 82 07
      ^^^^^
      descriptor pointer $0782
```

The descriptor itself is unchanged.

### Validation

- Original `PRDRIVERS` SHA256:
  `09e51f041e67fa58756c0c32a362bcff7119488af5070df884f4778fff86e3e0`
- R0 `PRDRIVERS` SHA256:
  `38695693478234d4821a0af9095e3bad64e574e31566256c5112a75c217990f9`
- Exactly **10 bytes** differ in each patched `.2mg` image.
- Both patched disks were re-opened as ProDOS filesystems and `PRDRIVERS` was
  re-extracted and verified.
- The ML84 descriptor bytes at `$0782` are byte-for-byte identical to the
  original.

### Disk hashes

R0 HD-install disk:

`41211d1a27320ab3be763b5f8f0853e3bb615654a6559e2f13f6661181fb54ef`

R0 main-app disk:

`ec80e9883d51906f7861442da6dc1151168e0bf0dbe615546adbfdc9e4647418`

## Hardware test order

For the cleanest first experiment, test the ML83A first if convenient. Its
wide carriage removes printable-width differences between the ML84 ancestor
and the 82A from the first test. Then test the 82A with artwork kept comfortably
inside an 8-inch graphics width.

In PSGS Setup select:

```
82A83A OGI
```

and select the actual interface/slot configuration normally used with the
printer. PSGS will regenerate its `PRINTER.DRIVER` from the selected printer
record plus the selected interface driver.

Use a simple monochrome design containing:

1. a large rectangle or 1-inch reference square;
2. a solid black region;
3. diagonals;
4. several horizontal lines crossing many raster-band boundaries; and
5. enough vertical height (4-6 inches) to make any 15/14 scaling obvious.

Record these observations independently:

- enters graphics / produces recognizable dots;
- horizontal scale and left-right registration;
- whether `$03` data collisions cause random command corruption;
- band-to-band carriage return alignment;
- inter-band gaps or overlap;
- measured vertical size versus intended size;
- clean graphics exit and end-of-page behavior.

## R1 decision tree

If R0 is recognizable and stable but ~7% tall:
- keep the Oki command tail unchanged;
- test vertical geometry compensation.

If isolated columns corrupt or graphics mode unexpectedly changes:
- trace/patch the descriptor's literal-ETX substitution fields.

If bands overprint without vertical movement:
- patch the per-band Oki graphics-feed control to explicitly use `ETX SO`.

If graphics mode never starts:
- reduce the entry sequence from `RS ETX` to the minimum OkiGraph I `ETX`
  sequence and retest.

If R0 is horizontally clipped on the ML82A only:
- keep protocol work separate from carriage/page-width handling and first
  validate on the ML83A.
