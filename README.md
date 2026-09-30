# The Print Shop GS — Okidata 82A/83A OkiGraph I

Experimental Apple IIgs printer-driver work for **Broderbund The Print Shop GS** targeting the **Okidata MICROLINE 82A and 83A equipped with OkiGraph I firmware**.

This project follows the completed Apple II Print Shop Color driver work in [`ppuskari/ThePrintShop-Okidata82a83a`](https://github.com/ppuskari/ThePrintShop-Okidata82a83a), but Print Shop GS uses a very different, data-driven printer architecture.

## R0 status

**R0 is a minimal hardware-proof build.** It repurposes Print Shop GS's existing `Okidata 84` printer selection as:

```text
82A83A OGI
```

The original ML84 descriptor pointer remains `$0782`, and the full 128-byte printer descriptor remains byte-for-byte unchanged. Only the 10-byte selector name in `PRDRIVERS` is replaced.

This isolates one question:

> Is Broderbund's existing ML84/Oki graphics descriptor already compatible enough with the 82A/83A OkiGraph I firmware to produce coherent output?

R0 is intentionally **not** a finished driver and is not presented as one.

## Why the ML84 is a strong ancestor

The existing PSGS ML84 descriptor already describes the same broad protocol family we recovered independently from OkiGraph I:

- seven-dot Oki graphics organization;
- 60 horizontal graphics columns/inch;
- `ESC % 9` programmable line spacing;
- `RS` / 10-CPI selection before graphics;
- ETX graphics state;
- ETX-STX graphics exit; and
- descriptor data strongly consistent with doubled ETX handling for a literal `$03` graphics byte.

The important known mechanical difference is vertical movement. Standard Oki 7-bit graphics uses a nominal **14/144-inch** band advance, while the physically validated 82A/83A OkiGraph I firmware advances **15/144 inch** per native graphics band. A successful R0 may therefore be coherent but approximately **7.14% too tall** over long vertical spans.

## R1 status

**R1 replaces the ML84 command fields with native 82A/83A OkiGraph I framing.**

It keeps PSGS's existing seven-dot / 60-column-inch encoder and literal-ETX escaping, but changes raster entry to `CR, ETX` and redefines the programmable movement record so the normal `$0E` raster-band movement emits:

```text
03 03 0E 03 02
```

That is native OkiGraph I: enter graphics, graphics feed + carriage return, then exit graphics. R1 changes no PSGS executable code and leaves the stock ML92/93 entry untouched. See [`docs/R1-ANALYSIS.md`](docs/R1-ANALYSIS.md).

## R3 status

**R3 traces and tests the PSGS 120-to-60 horizontal reducer without changing any OkiGraph I protocol bytes.**

Reverse engineering of `MF` shows that the Oki graphics-format flag (`1`) selects an **unsized streaming** graphics path: PSGS emits the descriptor's begin string and raw encoded raster data, but no width/count preamble. The two preceding optional descriptor blocks are horizontal positioning and color selection.

R3 therefore leaves the R2 native OkiGraph descriptor unchanged and changes one three-byte instruction in `MF`:

```text
$72F9: 9C 07 73   STZ $7307
     -> 20 25 75   JSR $7525
```

`$7525` is PSGS's existing helper that clears the 60-dpi reducer phase (`$73E7`) and both OR accumulators (`$7869/$786B`). This makes every raster row begin from a known horizontal reduction state.

See [`docs/R3-ANALYSIS.md`](docs/R3-ANALYSIS.md) and [`docs/R3-HARDWARE-TEST.md`](docs/R3-HARDWARE-TEST.md).

## R4 status

**R4 fixes a protocol bug in R1/R2/R3 vertical movement.**

PSGS passes a movement *distance* into its generic spacing routine; R2 had been inserting that value directly as an OkiGraph command byte. R4 caps the chunk at `$0E` and suppresses sub-`$0E` remainders so the printer only ever sees the validated native graphics feed command `03 0E`.

Compared with R2, R4 changes exactly two bytes: one descriptor byte and one branch displacement in `MF`. R3's reducer-reset diagnostic is not carried forward.

See [`docs/R4-ANALYSIS.md`](docs/R4-ANALYSIS.md).

## R5 status

**R5 returns to the coherent R2 baseline and sanitizes PSGS vertical movement without carrying R3 or R4 forward.**

The OkiGraph descriptor now uses a unique maximum movement chunk of `$0E`. A small MF compare hook rounds any positive sub-`$0E` remainder up to `$0E`, while larger requests continue through PSGS's existing chunk loop. The printer therefore receives only repeated, hardware-proven native OkiGraph movement sequences:

```text
03 03 0E 03 02
```

Unlike R4, small positioning requests are not discarded. Other stock printer descriptors retain their original movement semantics because none uses a `$0E` maximum chunk.

See [`docs/R5-ANALYSIS.md`](docs/R5-ANALYSIS.md) and [`docs/R5-HARDWARE-TEST.md`](docs/R5-HARDWARE-TEST.md).

## R9 status

**R9 is the first geometry-corrected build on top of the hardware-good R8 graphics path.**

R8 established clean persistent OkiGraph graphics, correct literal-ETX handling, coherent greeting cards/signs, and native `03 0E` band movement. The remaining defect was vertical output about 7.14% too tall because OkiGraph I physically advances each band origin by 15/144 inch instead of PSGS's logical 14/144 inch.

R9 uses Print Shop GS's own vertical phase-table resampler and expresses the correction exactly as:

```text
70 / 75 = 14 / 15
```

The phase schedule is:

```text
1 1 1 1 1 1 1 0 1 1 1 1 1 1 1
```

so fourteen printer rows are emitted per fifteen logical source rows. R8's printer protocol/state and horizontal 120→60 reducer are otherwise unchanged.

See [`docs/R9-ANALYSIS.md`](docs/R9-ANALYSIS.md) and [`docs/R9-HARDWARE-TEST.md`](docs/R9-HARDWARE-TEST.md).

## R11 status

**R11 moves the 14/15 vertical correction to the physical OkiGraph band-feed schedule.**

R8 remains the visual/raster baseline. R9/R10 source-row scaler changes are not carried forward. R11 keeps the stock 72/72 PSGS vertical source mapping and emits fourteen native `03 0E` feeds for every fifteen logical graphics-band transitions. The fifteenth transition exits graphics, performs CR only with no linefeed, and re-enters graphics on the next raster row.

```text
15 * 14/144 = 14 * 15/144
```

Test Paper Position uses the same exit + CR-only helper, so repeated registration tests should return the carriage left without moving the paper vertically.

See [`docs/R11-ANALYSIS.md`](docs/R11-ANALYSIS.md) and [`docs/R11-HARDWARE-TEST.md`](docs/R11-HARDWARE-TEST.md).

## Repository layout

```text
scripts/
  patch_psgs_okigraph_r0.py   Fail-closed R0 patcher

docs/
  R0-ANALYSIS.md              Driver architecture and descriptor analysis
  R0-HARDWARE-TEST.md         First hardware-validation procedure
  PROVENANCE.md               Source/provenance and redistribution boundaries

SHA256SUMS-R0.txt             Known hashes for R0 inputs/outputs
```

## Build R0

Python 3.10+ is sufficient; no third-party Python packages are required.

```bash
python scripts/patch_psgs_okigraph_r0.py \
  ORIGINAL.2mg \
  Print_Shop_GS_OkiGraphI_R0.2mg
```

The patcher fails closed unless the embedded `PRDRIVERS` payload exactly matches the known PSGS baseline and the ML84 selector, pointer, and descriptor are all where expected.

It also reopens and verifies the resulting ProDOS image and confirms that exactly the expected selector bytes changed.

## Hardware test

In Print Shop GS Setup, select:

```text
82A83A OGI
```

and then select the normal physical interface/slot configuration used by the printer.

The first hardware test should preferably be performed on an **ML83A** because its wide carriage removes one variable from the ML84-derived experiment. See [`docs/R0-HARDWARE-TEST.md`](docs/R0-HARDWARE-TEST.md) for the test pattern and measurements to record.

## Redistribution

This repository does **not** contain Broderbund Print Shop GS disk images, executables, manuals, or extracted proprietary program files. The patcher operates on a user-supplied original `.2mg` image and changes only the bytes documented in this repository.

## Project history

This work continues a broader effort to restore and extend Okidata support on vintage Apple systems. It also continues printer-driver ideas Petar had discussed with Rebecca Heineman, including IIgs printing work. Rebecca's enthusiasm for the Apple IIgs and for solving exactly this kind of low-level compatibility problem remains part of the spirit of the project.

## Current milestone

**R11 — physical 14/15 band-feed correction candidate**

R11 restores R8's clean source/raster geometry and tests the vertical correction at the physical feed layer: fourteen 15/144-inch OkiGraph feeds for every fifteen logical 14/144-inch band transitions. Hardware validation is pending.