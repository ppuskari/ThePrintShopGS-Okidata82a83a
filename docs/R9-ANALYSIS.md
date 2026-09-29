# Print Shop GS — Okidata 82A/83A OkiGraph I — R9 analysis

## Starting point

R8 is the first hardware baseline where greeting cards and signs print coherently
with clean graphics starts, persistent OkiGraph state, correct literal-ETX
handling, and no text-style blank line between raster bands.

Hardware still shows a geometry problem: vertical output consumes essentially
the full 11-inch sheet while horizontal margins remain present. This matches
the already measured OkiGraph-I band geometry:

```text
logical PSGS/ML84 band origin step: 14/144 inch
physical OkiGraph-I band origin step: 15/144 inch
physical expansion:                 15/14 = 1.071428571...
required source correction:         14/15 = 0.933333333...
```

R9 changes only vertical source scaling. R8 printer protocol/state is frozen.

## PSGS already contains the required vertical resampler

The printer descriptor parser stores the vertical-resolution word in `$A064`.
Printer setup at `MF:$752F` then builds a vertical phase table at `$794D`.

The relevant sequence is:

```text
$753B  LDA $A064       ; descriptor vertical value
$753E  STA $08
$7540  TAY
$7541  LDX #$0048      ; logical vertical base = 72
$7544  LDA #$794D
$7547  JSR $7943       ; -> table generator at $7DAD
```

A second copy rebuilds the table after PSGS applies its higher-level percentage
scaling:

```text
$758C  LDX #$0048      ; logical vertical base = 72
$758F  LDY $08
$7591  LDA #$794D
$7594  JSR $7943
```

The horizontal 120-to-60 reducer is separate and remains untouched:

```text
$75A2  LDX #$0078      ; 120 horizontal logical samples/inch
$75A5  LDA #$73E9
$75A8  JMP $7943
```

Thus R9 can use PSGS's own scaler rather than adding another raster routine.

## Exact 14/15 ratio using integer inputs

Using a nominal 67 or 68 DPI descriptor would only approximate the required
67.2-row/inch equivalent. Instead R9 expresses the ratio itself:

```text
R8 vertical ratio: 72 / 72 = 1.0
R9 vertical ratio: 70 / 75 = 14 / 15 exactly
```

R9 changes the private Oki descriptor's vertical word from 72 to 70 and changes
only the two vertical phase-table bases from 72 to 75.

The PSGS table generator at `$7DAD` then creates this 15-step pattern:

```text
1 1 1 1 1 1 1 0 1 1 1 1 1 1 1
```

That is fourteen emitted printer rows for every fifteen logical source rows.
The dropped row is phase-distributed by PSGS's existing accumulator rather than
always removed at a band boundary.

For a nominal 11-inch, 72-row/inch logical height:

```text
792 logical rows * 14/15 = 739.2
```

The integer phase table yields 739 rows over the first 792-row interval, with
the fractional phase carried normally by the existing scaler.

## Why this matches the OkiGraph-I physical lattice

OkiGraph I still prints seven host-addressable pins at these physical positions
within a band:

```text
0/144, 2/144, 4/144, 6/144, 8/144, 10/144, 12/144 inch
```

and the next band origin is 15/144 inch.

R9 does not alter that hardware-native lattice. Instead it supplies 14/15 as
many logical vertical source rows to the existing seven-pin band packer, which
cancels the average 15/14 physical expansion.

This is materially different from merely calling the printer "67 DPI": it uses
an exact rational phase schedule inside PSGS's own scaler while leaving native
OkiGraph banding untouched.

## R8 protocol/state remains intact

R9 does not change graphics entry/state handling, persistent graphics state,
native `03 0E` band movement, literal raster `$03 -> 03 03`, encoder 2,
the 60-column/inch horizontal reducer, or the ProGrappler/interface path.

Relative to R8, only one PRDRIVERS byte and two MF operand bytes change:

```text
private descriptor Y low byte: $48 -> $46   ; 72 -> 70
MF:$7542:                      $48 -> $4B   ; base 72 -> 75
MF:$758D:                      $48 -> $4B   ; base 72 -> 75
```

No opcodes change. No code cave is added. No horizontal-scaler byte changes.

## Hashes

```text
PRDRIVERS.R9
e37d0eb5f268a10f3e1ea3103a73791023d3a54bee87de2bb544eb34a60e2725

MF.R9
e4aeac71a399ad11f935aed0c94018d02991e7bb6aba6b3bf323129fb8c3216f

R9 Main
97d33d1fbfe9fa6b733fddd4f80cda2bdca9e4362aa2eb10b899e7cda53db03f

R9 HD Install
d10bfbc6cabd5390b606e08a8f2e2485f3fc2752461b913c7c823a7bd38dfdc0

R9 patcher
2b27366e9ac7a6170c2bf4caa12bf68bd2793daea24bbd3cb066c5a6562c95ca
```

Both output images were regenerated from the untouched known source disks,
reopened as ProDOS filesystems, and their `MF` and `PRDRIVERS` payloads were
re-extracted and verified.

## Expected hardware result

R8's clean graphics should remain unchanged horizontally and at band starts.
The only intended visible change is vertical compression by exactly 14/15.

If an R8 job physically consumed about 11.000 inches vertically, the first-order
R9 expectation is:

```text
11.000 * 14/15 = 10.2667 inches = 260.77 mm
```

which restores about 18.63 mm of total vertical whitespace relative to a full
279.4 mm Letter sheet. Exact top/bottom distribution still depends on the Print
Shop product layout and paper-origin behavior.
