# R1 hardware test — Print Shop GS + 82A/83A OkiGraph I

R1 tests native OkiGraph I command/state handling while leaving the rest of
Print Shop GS intact.

## Setup

1. Boot the R1 floppy image (or install from the R1 HD-install image).
2. Open printer setup.
3. Select `82A83A OGI`.
4. Select the same ProGrappler parallel interface/slot that worked in R0.
5. Do not change printer DIP switches or ProGrappler configuration solely for
   this test.

## Primary test

Repeat the same ready-made Christmas card used for R0.  That makes the R0/R1
comparison useful.

Record:

- Does the first upper-left raster panel remain recognizable?
- After the first raster row, does the printer now make a normal small native
  band advance instead of a text-height LF?
- Do subsequent rows remain coherent instead of becoming patterned junk?
- Do successive bands return to the same left margin?
- Are there recurring white gaps or overlaps between bands?
- Does the printer cleanly leave graphics mode at page/panel transitions?
- Does the job finish without the parser becoming confused?

## If the raster is coherent

Measure one known vertical feature.  R1 may still be approximately 7.14% tall:

```text
OkiGraph I band origin = 15/144 inch
nominal PSGS/Oki model = 14/144 inch
ratio                  = 15/14 = 1.071428...
```

That is not an R1 protocol failure.  It would mean the next problem is the
nonuniform OkiGraph I physical Y mapper.

## If corruption remains

The exact transition matters.  Note whether corruption begins:

- immediately at the first graphics byte;
- exactly at the first band boundary;
- after several correct bands;
- only at a panel/page transition; or
- at an apparent literal-ETX data column.

A photo of the first 2–3 inches of output is especially useful.

## Test Paper Position

The known PSGS Test Paper Position defect is intentionally unchanged in R1.
It may print the reference dots and then advance the paper, losing the useful
physical alignment position.  Do not use that behavior to judge the graphics
protocol patch.
