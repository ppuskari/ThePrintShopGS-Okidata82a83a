# Print Shop GS — Okidata 82A/83A OkiGraph I — R5 analysis

## R5 objective

R4 proved that simply discarding PSGS movement requests smaller than `$0E`
was wrong: the printer-test `WELCOME` graphic collapsed/overprinted because
those small positioning requests are meaningful.

R5 returns to the coherent R2 baseline and fixes the underlying protocol
problem without carrying R3 or R4 forward.

## The protocol problem

The R2 OkiGraph movement descriptor is only valid when its dynamic value is
`$0E`:

```text
03 03 0E 03 02
```

Starting in text state this is:

```text
03       enter graphics
03 0E    native OkiGraph graphics feed + carrage return
03 02    exit graphics
```

PSGS's generic movement engine, however, can request many positive distances.
R2 therefore sometimes generated streams such as:

```text
03 03 01 03 02
03 03 07 03 02
03 03 0D 03 02
```

Those values are not programmable OkiGraph distances. They put arbitrary
values into OkiGraph command state and are a strong match for the startup
blips, overprint, and unusual carriage motion seen in the printer test.

R4 suppressed sub-`$0E`~ remainders. Hardware showed that was also wrong,
because it removed real positioning movement and made the `WELCOME` graphic
substantially worse.

## R5 strategy: preserve movement, quantize it to proven native feeds

R5 sets the OkiGraph descriptor's maximum movement chunk to `$0E` and lets
PSGS keep its normal chunk loop. A small comparison hook changes only this
OkiGraph driver's positive remainder behavior:

```text
1..13  -> 14
14     -> 14
15..27 -> 14 + 14
28     -> 14 + 14
...
```

So the physical result is:

```text
feeds = ceil(requested_distance / 14)
```

Every emitted movement is therefore one or more copies of the only movement
command we have actually proved on 82A/83A OkiGraph I hardware:

```text
03 03 0E 03 02
```

R5 is intentionally about clean command state, not final geometry. Small PSGS
movements are rounded to one 15/144-inch native band, so final vertical
resampling remains a later step.

## Why this remains isolated from stock printers

The original PSGS printer database uses maximum movement values:

```text
$31, $3F, $55, $7F
```

No stock descriptor uses `$0E`.

R5 changes only the repurposed OkiGraph descriptor to `$0E`. The MF hook checks
that runtime value. Any stock printer therefore receives the original `CMP
$7861` semantics unchanged.

## MF hook

The original vertical routine begins at `$75C7`:

```text
$75C7  CD 61 78     CMP $7861
$75CA  90 10        BCC $75DC
$75CC  F0 0E        BEQ $75DC
...
```

R5 changes only the first instruction:

```text
$75C7  20 67 7E     JSR $7E67
```

The original BCC/BEQ/chunk loop at `$75CA` is unchanged.

`$7E67-$7E8C` is zero padding in the shipped MF image immediately before the
next string/data region. No JSR/JMP target into that range exists in the
original MF. R5 uses 27 bytes there:

```asm
        PHA
        LDX $7861
        CPX #$000E
        BNE normal
        PLA
        CMP #$000E
        BCS compare
        LDA #$000E
compare CMP $7861
        RTS
normal  PLA
        CMP $7861
        RTS
```

Thus the caller sees the same condition-code contract as the original `CMP`,
except that this one unique driver rounds positive sub-band values up to `$0E`.

The high-level MF path at `$72E7` already tests the pending movement for zero
before invoking `$73CC`, so the OkiGraph vertical hook is expected to receive
positive distances in this path.

## R3/R4 status

R3's reducer reset is **not** present in R5. Hardware showed no change.

R4's BCC-to-RTS remainder suppression is **not** present in R5. The stock bytes
at `$75CA` are restored/retained:

```text
90 10
```

R5 is therefore R2 plus the native-movement quantizer only.

## Hashes

```text
MF.R5
5bc87fe4bcd42efae022240a61027488ebd37a6d112527f0491fbc9722cdc846

PRDRIVERS.R5
e535b0eae5c9b5e0fd54cc192369d7dba323254ee3a4f8b702ed65e9e49017b0

R5 Main
6a6aaa59d14ad0e7fb7d22a8903a19cfcc083741f3c407b261a48164d9cc5f7a

R5 HD Install
bdf687d665d4c13670609ea334cad7272865d2d6c6510b7d64f89e97239d3fbf

R5 patcher
6d87d0750534406994265ebbe8ec34e1a4ccf83c530a15e6c5dd48aac82342af
```

Each R5 image differs from the original in 55 physical bytes. Compared with
R2, R5 differs in 28 physical bytes: the max-movement marker, the three-byte
MF compare hook, and the nonzero bytes of the 27-byte code hook.
