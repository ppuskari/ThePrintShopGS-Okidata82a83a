# R9 hardware test — exact 14/15 vertical scaling

R9 is a geometry-only delta from the hardware-good R8 graphics baseline.

## Setup

Power-cycle/reset the printer before the first R9 job, then use the same:

- `82A83A OGI` printer selection;
- ProGrappler parallel interface/slot;
- printer DIP/interface settings used for R8.

Do not change paper loading solely for R9; use the same physical start position
used for the successful R8 greeting-card/sign tests.

## 1. Repeat the same greeting card

Use the same ready-made Christmas card used for R8.

Confirm first that R8's good behavior remains: no leading extra pixel/blip, no
`!`-like extra first column, no one-column right shift, no text-line blank gap
between raster bands, and coherent graphics from top to bottom.

Then measure the total vertical printed extent as accurately as practical.

R9 applies exactly 14/15 of R8's logical vertical row count. If R8 occupied
approximately the full 11-inch/279.4-mm sheet, the rough expected R9 extent is:

```text
10.2667 inches
260.77 mm
```

Do not expect exact centering solely from this number; top/bottom positioning is
separate from scale.

## 2. Repeat the same sign

The sign is useful because R8 already showed sensible left/right margins of
about 15.2 mm. Horizontal geometry should be unchanged in R9.

Record left margin, right margin, top margin, bottom margin, and total printed
height. If left/right margins change materially, stop: R9 should not affect
horizontal scaling at all.

## 3. Visual vertical-quality check

R9 uses PSGS's own phase table:

```text
1 1 1 1 1 1 1 0 1 1 1 1 1 1 1
```

so one logical vertical row is omitted per fifteen source rows. Inspect diagonal
and curved graphics for any objectionable periodic horizontal white line.

R9 is successful if R8's graphics cleanliness and horizontal dimensions remain
unchanged, vertical extent contracts by approximately 14/15, restored top/bottom
whitespace looks plausible, and no objectionable periodic artifact appears.
