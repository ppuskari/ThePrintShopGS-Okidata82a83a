# Provenance and redistribution boundaries

## Original software

The Print Shop GS program, disk images, manuals, graphics libraries, and other original Broderbund assets are proprietary historical software and are **not redistributed by this repository**.

Development and reverse engineering were performed from user-supplied archival `.2mg` images and manuals.

## Repository contents

This repository contains only derived engineering material created for the Okidata 82A/83A OkiGraph I compatibility project, including:

- analysis and documentation;
- a patching utility;
- expected checksums;
- offsets and small command/descriptor excerpts necessary to describe the interface; and
- hardware-test procedures.

It does not contain a complete original or patched Print Shop GS disk image.

## R0 modification

R0 changes only the printer-selection text inside `PRDRIVERS`:

```text
original: Okidata 84
R0:       82A83A OGI
```

Both strings are 10 bytes. The ML84 descriptor pointer remains `$0782`, and the descriptor itself remains unchanged.

## Related independent OkiGraph I work

The OkiGraph I protocol and physical geometry used to interpret the PSGS data are independently documented in:

- `ppuskari/Okidata-Microline-82A-83A`
- `ppuskari/ThePrintShop-Okidata82a83a`

The physical OkiGraph I model established there includes:

```text
7 host-addressable graphics pins
60 graphics columns/inch
15/144-inch native graphics-band advance
ETX graphics state
ETX $02 graphics exit
ETX $0E graphics feed + carriage return
```

Those findings are derived from firmware analysis and physical printer validation rather than from Print Shop GS.

## Reproduction

A user with a matching original Print Shop GS `.2mg` image may reproduce R0 by running:

```bash
python scripts/patch_psgs_okigraph_r0.py ORIGINAL.2mg R0.2mg
```

The script validates the expected `PRDRIVERS` baseline before modifying anything and refuses to patch unknown variants.
