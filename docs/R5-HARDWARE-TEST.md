# R5 hardware test

Use the same `82A83A OGI` + ProGrappler configuration.

## 1. Printer/Test Paper Position test first

Compare directly with R2 and R4.

Watch for:

- the tiny extra blip before the first top-pin alignment dots;
- the roughly four-column overprint at the start of `WELCOME`;
- the strange back-and-forth / apparent partial double-printing;
- whether the rest of `WELCOME TO THE PRINT SHOP` is coherent.

R5 does **not** discard small movements as R4 did. Any positive movement less
than `$0E` becomes one native OkiGraph `$03 $0E` feed. Therefore the paper may
advance by one small native band (15/144 inch, about 0.104 inch) where R2/R4
appeared stationary; a large text-style line feed should not return.

## 2. Same ready-made Christmas card

Inspect the known upper-left panel locations:

- first raster band: leading extra dot/blip;
- final affected band: `!`-looking extra column;
- one-column right shift after either artifact.

Also note whether overall carriage motion sounds/looks cleaner than R2.

## 3. Do not judge final vertical page fit yet

R5 deliberately preserves the native 15/144-inch OkiGraph band movement and
does not yet perform the final nonuniform vertical resampling. The page can
still consume essentially the full 11-inch height.

## Decision

If printer-test motion and the leading artifacts clean up, keep R5 as the
native-command baseline and proceed to final vertical mapping/scaling.

If command motion is clean but isolated leading columns remain, freeze the R5
movement fix and trace only first-column/run startup behavior next.
