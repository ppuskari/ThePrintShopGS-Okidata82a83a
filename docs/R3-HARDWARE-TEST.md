# R3 hardware test — horizontal reducer row reset

R3 keeps every OkiGraph I protocol byte from R2 and changes only the PSGS
horizontal reducer state at raster-row start.

## Setup

Use the same printer and interface configuration that produced coherent R2
output:

- `82A83A OGI`
- Okidata MICROLINE 82A or 83A with OkiGraph I
- same ProGrappler parallel slot/interface settings

Do not change printer DIP switches or ProGrappler settings for this comparison.

## Primary A/B test

Print the same ready-made Christmas card used for R1 and R2.

Inspect the upper-left panel closely at exactly the two known R2 sites:

1. the very first raster band, where an extra left-edge graphics column appeared
   before the intended holly/artwork and shifted the rest of that band right;
2. the final graphics band of that panel, where a different extra left-edge
   column looked like `!` and likewise shifted that band right.

Record whether each extra column is:

- gone;
- still present but changed;
- still present exactly as before; or
- moved to another band.

Also compare the left edge of all ordinary intervening bands.  R3 should not
change the artwork, horizontal scale, native band spacing, or graphics-state
stability.

## Test Paper Position

Repeat Test Paper Position once.  R3 does not change the R2 movement descriptor,
so the useful no-large-linefeed behavior should remain.

## Vertical size

Ignore final vertical fit for this test.  R3 intentionally keeps the R2
15/144-inch native band movement without vertical resampling, so the page can
still consume essentially the full 11-inch height with no intended border.
That will be corrected only after the extra horizontal column problem is closed.

## Interpretation

If the two unwanted columns disappear, the cause was stale PSGS 60-dpi reducer
phase/OR state at selected row boundaries.

If they remain unchanged, do not alter OkiGraph framing.  The next R4 target is
the PSGS deferred-leading-blank replay path (`$7309` / the higher-level raster
call around `$7D61`), because the descriptor trace proved that the Oki special
graphics format transmits no width/count preamble.
