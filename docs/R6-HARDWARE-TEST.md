# R6 hardware test

R6 changes graphics-state handling substantially, so begin from a known printer
state.

1. Power-cycle/reset the ML82A/83A before the first R6 print. This matters after
   the failed R5 job may have left the OkiGraph parser in an unknown state.
2. Boot the R6 floppy.
3. In Setup select `82A83A OGI` and the same ProGrappler parallel interface.
4. For the cleanest diagnostic, do one print test per fresh printer reset while
   R6 is experimental.

## Test 1 — same Christmas card

This is the primary R6 gate because R2 already made it coherent.

Inspect the upper-left panel for the two known faults:

- the tiny extra graphics blip before the first intended column;
- the `!`-looking extra first column on the last affected band;
- the one-column right shift following either artifact.

Also watch carriage behavior. Normal raster bands should now remain in graphics
state and move with native `03 0E`, rather than exit/re-enter for every band.

Do not judge final page height yet. R6 still uses the native 15/144-inch band
advance without final vertical resampling.

## Test 2 — printer/alignment test

After a fresh printer reset/reselection, run the printer test and note:

- whether the leading top-pin alignment blip remains;
- whether `WELCOME` still has the block over its W;
- whether the carriage still makes abnormal repeated/back-and-forth passes;
- whether any old large text-style line feed reappears.

R6 uses the stock ML84 programmable text movement only for movement requests
other than `$0E`, so this test may still expose a separate OkiGraph text-spacing
compatibility problem. That is intentionally separated from the normal raster
band state machine.

## Important experimental limitation

R6's private state is initialized when Setup copies the selected 128-byte
printer descriptor. Graphics-end is deliberately empty across normal raster
rows. Until final job-close handling is added, use a printer reset plus fresh
R6 Setup selection between independent diagnostic print jobs if behavior ever
appears stateful after a previous job.
