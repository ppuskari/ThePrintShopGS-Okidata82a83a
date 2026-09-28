# R1 — native OkiGraph I descriptor test

R1 replaces the sacrificial ML84 descriptor command fields with native
MICROLINE 82A/83A OkiGraph I framing while preserving Print Shop GS's existing
7-dot / 60-column-inch raster conversion.

## Changes from the original PSGS image

- selector: `Okidata 84` -> `82A83A OGI`
- graphics begin: `1E 03` -> `0D 03` (CR, ETX)
- programmable movement: `ESC % 9 <n> LF` -> `03 03 <n> 03 02`
- graphics end remains `03 02`
- literal ETX escape remains `03 -> 03 03`
- encoder remains PSGS selector 2
- no executable code changes
- stock ML92/93 entry remains untouched

For the normal seven-dot raster band (`n=$0E`), R1 emits:

```text
03 03 0E 03 02
```

which gives native OkiGraph I graphics feed + carriage return between raster
rows while returning to text state afterward.

Exactly 18 bytes differ in each generated disk image.

## Status

Hardware-test build.  Protocol stability is the goal; final 15/144-inch
nonuniform vertical geometry and the Test Paper Position post-marker feed are
not yet corrected.
