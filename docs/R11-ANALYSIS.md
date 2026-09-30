# R11 analysis — move 14/15 correction to physical band feeds

R8 is the visual baseline: clean persistent OkiGraph graphics, correct literal ETX handling, 60-column/inch horizontal mapping, and stock PSGS 72/72 vertical source mapping.

R9/R10 altered the source-row scaler, but hardware still showed the physical seven-pin band structure and vertical stretch. R11 restores the R8 source geometry and corrects the actual 15/144-inch OkiGraph band movement.

The exact ratio is:

```text
15 logical transitions * 14/144
= 14 native feeds * 15/144
```

R11 keeps a private 15-transition countdown. Transitions 1–14 emit `03 0E`. Transition 15 performs a zero-feed merge: `03 02` exits graphics, CR returns the carriage with no linefeed, state is cleared, and the next raster row re-enters graphics at the same vertical origin.

The private selected-driver block remains entirely in `$0300-$037F`; no MF code cave is used. Test Paper Position calls the same exit+CR-only helper, fixing R10's carriage-left regression without moving the paper vertically.

R11 leaves both PSGS vertical scaler bases at 72, descriptor Y at 72, and the horizontal 120→60 reducer unchanged.
