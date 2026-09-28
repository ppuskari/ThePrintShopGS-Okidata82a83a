# Print Shop GS — Okidata 82A/83A OkiGraph I — R3 analysis

## Why R3 exists

R2 left the native OkiGraph I protocol stable and sustained graphics coherent,
but two isolated raster bands still began with one extra graphics column.  The
extra column was visibly before the intended artwork and displaced the remainder
of each affected band one column to the right.  That proved the artifact was
extra information entering the raster stream, not part of the intended image.

R3 therefore traces Print Shop GS from its printer descriptor parser through the
actual graphics-data path before changing anything.

## Descriptor trace: the Oki path does not send a width/count

The printer descriptor parser in `MF` is centered around `$7462..$752E`.
Relevant helper routines are:

```text
$775D  get byte
$7768  get word
$7771  parse/skip length-prefixed string
$7826  parse [prefix string][value-spec byte][suffix string]
$777F  encode a dynamic value according to the value-spec byte
$77FA  output a length-prefixed string
$781C  output prefix + encoded value + suffix
```

After the fixed geometry, initialization, CR, and vertical-movement fields,
there are three optional areas.

### Optional block 1 — horizontal positioning

The first optional block is stored through `$7857`.  When present it has the
same prefix/value/suffix structure parsed by `$7826`.

Higher-level raster code calls this capability only when deferred leading blank
columns reach the horizontal-positioning threshold.  It is therefore a
horizontal skip/positioning facility, not a graphics byte-count preamble.
The ML84/Oki record has this block disabled.

### Optional block 2 — color selection

The second optional block is stored through `$7859`.  It contains a command
prefix, a four-byte color map, and a suffix.  Its capability flag is separate
from graphics sizing.  The Oki record also has this disabled.

### Graphics format flag

The next byte, referenced through `$785B`, selects one of two graphics-command
formats.

When the byte is zero, Print Shop GS uses the conventional **sized** graphics
format.  The descriptor contains a prefix, a dynamic size/count encoding byte,
and a suffix.  The graphics-begin routine encodes the requested row width and
transmits it as part of the printer command.

The Oki descriptor uses a nonzero flag (`$01`).  This selects the alternate
**unsized streaming** format:

```text
flag
begin-string
end-string
special-trigger-byte
special-replacement-string
encoder selector
```

For this path, `MF:$7682` outputs only the begin string.  It does **not** emit a
width or count.  The graphics-data routine later applies the special-byte
replacement (`$03 -> $03 $03`) and the selected seven-dot encoder, and
`MF:$769C` outputs the end string.

This is decisive: the extra first-column artifacts observed on hardware are
**not** graphics width/count bytes produced by the Oki descriptor's optional
fields.

## Higher-level raster path

The relevant printer jump-table entries include:

```text
$73C0 -> $7462  descriptor initialization
$73C3 -> $752F  printer geometry / reducer setup
$73C9 -> $75B8  carriage return
$73CC -> $75C7  vertical movement
$73CF -> $75E7  optional horizontal positioning
$73D2 -> $7609  color selection
$73D5 -> $762D  graphics begin
$73D8 -> $769C  graphics end
$73DB -> $76B0  graphics data
```

The high-level per-raster-row setup begins at `$72F3`:

```text
$72F3  STA $7303
$72F6  STX $7305
$72F9  STZ $7307
$72FC  STZ $7309
$72FF  STZ $730B
$7302  RTS
```

A whole-file reference search showed that `$7307` is written here but never
read anywhere else in `MF`; this three-byte `STZ` is therefore available for a
same-size diagnostic hook.

`$7309` is the deferred-leading-blank counter and `$730B` tracks whether
printer graphics have started for the current row.

## The 120-to-60 horizontal reducer

The Oki record requests 60 horizontal graphics columns/inch, while PSGS's
logical renderer works at the higher internal horizontal sampling rate.  The
printer setup at `$752F` therefore enables the 120-to-60 reduction path and
builds a reduction table.

The graphics-data routine around `$76B0` uses three persistent variables while
combining source columns:

```text
$73E7  reduction phase/index
$7869  first OR accumulator
$786B  second OR accumulator
```

Depending on the reduction-table phase, source columns are OR-accumulated and
an output printer column is emitted.  After an emitted combined column, the
accumulators are cleared.

The ordinary carriage-return routine at `$75B8` resets all three reducer
variables.  Descriptor initialization also contains an existing reset helper at
`$7525`:

```text
$7525  STZ $73E7
$7528  STZ $7869
$752B  STZ $786B
$752E  RTS
```

The per-row setup at `$72F3`, however, did not explicitly call that reset helper
before deferred blank replay and raster data began.

Given the hardware symptom — one unwanted printer column followed by a
one-column right shift, with the unwanted dot pattern changing on different
bands — stale reducer phase or OR carry is a substantially better fit than a
fixed printer command byte.

## R3 patch

R3 leaves the entire R2 printer descriptor byte-for-byte unchanged.  It changes
one three-byte instruction in `MF`:

```text
original at $72F9:
9C 07 73     STZ $7307

R3:
20 25 75     JSR $7525
```

The replaced `$7307` state word has no read references, while `$7525` is already
Print Shop GS's own reducer-reset sequence.  The patch therefore resets the
60-dpi phase and both OR accumulators at the beginning of every raster row
without adding a code cave or changing program size.

## OkiGraph I protocol remains exactly R2

R3 intentionally does not touch the printer protocol:

```text
graphics begin:        03
literal raster $03:    03 03
native band movement:  03 03 <n> 03 02    (normally n=$0E)
graphics end:          03 02
encoder:               PSGS encoder 2
horizontal pitch:      60 columns/inch
```

For a normal raster band, the movement stream remains:

```text
03 03 0E 03 02
```

which is OkiGraph I enter, native graphics feed + carriage return, and exit.
The physically measured 15/144-inch band-origin movement is therefore unchanged.

## Integrity and hashes

Original `MF`:

```text
12b35bc7e4bfa08268399a2b8ef65750230ff8625f72302106677594977ff7e3
```

R3 `MF`:

```text
ef7c6a593dca2617556edeaa29f9c190642e84bb07afec142322271967d08a71
```

R3 retains the exact R2 `PRDRIVERS`:

```text
fbfed119fcfb2cfcc4d37e2d20453c3b561f7a91faac01be34c1bf4b840112b1
```

R3 patcher:

```text
2bd571d87bc52fb0a6f16336059906b2282d42e89357c02e9755fdd431108d74
```

Main floppy R3:

```text
e08a875e3c6bae3970e39419e9699e28564c8bcde32ff0a6f887eb9c8950996a
```

v1.1 HD-install R3:

```text
d6eb3898bae9ef54cd09a179368abe1bbec40bd14aa039b7232d38a16810d4e7
```

Each R3 disk differs from its original in 30 bytes total: 27 bytes are the R2
`PRDRIVERS` patch and exactly 3 bytes are the `MF` row-reset hook.  Compared
with R2, each R3 disk differs in exactly those three `MF` bytes.

Both generated disks were reopened as ProDOS filesystems; `MF` and `PRDRIVERS`
were re-extracted and verified.  The main and HD-install images contain the same
patched `MF` and `PRDRIVERS` payloads.

## R3 hardware decision

Print the same ready-made Christmas card used for R1/R2.

If the two extra first columns and their one-column right shifts disappear,
R3 confirms that horizontal reducer phase/carry leaked across selected raster
row boundaries.

If the artifacts remain unchanged, the next diagnostic should leave the
OkiGraph protocol frozen and move one level higher to the deferred-leading-blank
replay path (`$7309`, including the call around `$7D61`).  That path can prepend
logical zero columns before real artwork and is the next plausible source of an
extra reduced printer column.

Vertical scaling is intentionally not changed in R3.  The page is expected to
remain physically too tall because the final nonuniform 15/144-inch OkiGraph I
Y mapping has not yet been resampled.
