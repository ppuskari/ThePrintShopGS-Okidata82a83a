# R6 — persistent OkiGraph graphics-state test

R6 returns to the original Print Shop GS baseline and replaces the sacrificial
ML84 selector with a private 128-byte `82A83A OGI` descriptor block appended
inside PRDRIVERS' already-allocated six data blocks.

Normal `$0E` raster-band movement now stays in OkiGraph graphics state:

```text
03        enter once
[raster]
03 0E     native graphics feed + CR; remain active
[raster]
03 0E
...
```

Per-row PSGS graphics-end and CR strings are empty. A fresh graphics begin is
suppressed while the private active state is set. Literal raster `$03` remains
escaped as `$03 $03` through PSGS encoder 2.

For non-`$0E` vertical movement while active, R6 exits graphics (`03 02`), homes
with CR, and falls back to the original ML84 programmable text movement. This is
intentionally conservative; final OkiGraph vertical mapping is still pending.

R6 does not carry R3, R4, or R5 forward and does not use the questionable
`$7E67` region from R5.
