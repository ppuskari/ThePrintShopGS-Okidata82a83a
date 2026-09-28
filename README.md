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

**R1 — native OkiGraph I descriptor protocol/banding test**

The immediate hardware question is whether the same Christmas-card test that failed after the first rows in R0 now remains coherent across raster bands. Final nonuniform 15/144-inch vertical geometry and the Test Paper Position post-marker feed remain later work.

**R0 — ML84 descriptor compatibility proof**

Next milestone depends on hardware results. If the output is coherent but vertically stretched, R1 will concentrate on OkiGraph I's 15/144-inch band-origin geometry while preserving the already-compatible Oki command framing.
