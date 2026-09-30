# R11 — physical 14/15 OkiGraph band-feed correction

R11 returns to the hardware-good R8 source/raster geometry and moves the vertical correction to the physical OkiGraph feed schedule.

OkiGraph I native `03 0E` advances 15/144 inch while PSGS's logical seven-pin band model is 14/144 inch. R11 emits fourteen native feeds for every fifteen logical band transitions. On the fifteenth transition it emits `03 02`, performs CR only with no linefeed, clears graphics state, and re-enters graphics on the next raster row.

```text
15 * 14/144 = 14 * 15/144
```

R9/R10 source-scaler edits are absent; the stock 72/72 vertical source mapping from R8 is restored.

Test Paper Position uses the same exit + CR-only helper, so the carriage returns left without vertical paper movement.

R11 is a hardware-test candidate, not yet a final release.
