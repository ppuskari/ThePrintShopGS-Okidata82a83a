# R11 hardware test

R11 is based on the visually clean R8 raster/source path. R9/R10 source-row resampling is not present.

First power-cycle/reset the printer and select `82A83A OGI` + ProGrappler.

## Test Paper Position

Run it twice without moving paper or carriage. Each invocation should print one dotted registration row, exit graphics, return the carriage left, and make **no vertical feed**. The second invocation should print on the same vertical registration line.

## Sign

R11 uses:

```text
transitions 1..14 : 03 0E native feed + CR
transition 15     : 03 02, CR only, no feed
repeat
```

Measure total height and top/bottom margins. Left/right geometry should remain the same as R8. The R9/R10 bare source-row artifact should be gone. Every fifteenth merge may look slightly darker because two logical bands share one physical origin.

## Greeting card

Confirm R8's clean left edge remains: no startup blip, no extra first column, no one-column shift, and no text-like blank line between bands. Measure total vertical extent.

R11 tests only whether the 7.14% vertical error belongs at the physical feed layer. If height is correct but the every-fifteenth merge is visually objectionable, the next refinement should blend the two logical bands while retaining the proven 14/15 feed ratio.
