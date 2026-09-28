# Print Shop GS — Okidata 82A/83A OkiGraph I — R1 analysis

## R1 objective

R0 proved that the Print Shop GS floppy remains bootable, the repurposed ML84
selector is usable, and the ProGrappler interface path is independent of the
printer descriptor.  Hardware testing also proved that the stock ML84 command
record is not suitable for 82A/83A OkiGraph I: the first raster rows appeared,
then text-style paper movement and patterned raster corruption followed.

R1 keeps the sacrificial ML84 selector slot but replaces its command fields
with the native OkiGraph I framing already proven on physical 82A/83A hardware.
It does **not** use or replace the stock ML92/93 entry.

## PSGS architecture recovered

`PRDRIVERS` contains the printer-selection table followed by printer records.
The stock ML84 entry points to `$0782`.

SETMAKE's printer path copies exactly 128 bytes from the selected PRDRIVERS
record to the live printer-driver workspace.  The interface driver is selected
and built separately, so the ProGrappler path remains unchanged.

The main Print Shop GS executable (`MF`) interprets the printer descriptor.
The relevant operations are:

- graphics begin;
- graphics end;
- graphics-byte output;
- programmable vertical movement;
- direct interface byte output.

The stock ML84 record selects PSGS encoder 2.  Reverse engineering shows that
this encoder already provides the Oki seven-dot transform and the record's
special-byte definition maps a literal `$03` graphics byte to `$03 $03`.
Those parts match the hardware-proven OkiGraph I path and are retained.

## Stock ML84 record

The 34-byte record beginning at PRDRIVERS `$0782` parses as:

```text
stride                 00
word0                   0000
pins                    07
horizontal resolution   003C = 60
vertical logical res.   0048 = 72
max movement chunk      3F
colors                  00
init                    empty
CR                      0D
movement prefix         1B 25 39     (ESC % 9)
movement spec           81           (one raw binary byte)
movement suffix         0A           (LF)
optional fields         00 00
graphics flag           01
graphics begin          1E 03        (RS, ETX)
graphics end            03 02        (ETX, STX)
special trigger         03
special replacement     03 03
encoder                 02
```

R0 therefore used the correct general raster family (7 pins, 60 columns/inch)
but the wrong line-movement / state transitions for OkiGraph I.

## R1 native OkiGraph I changes

R1 changes only two descriptor command definitions.

### 1. Raster-row entry

Stock ML84:

```text
1E 03     RS, ETX
```

R1:

```text
0D 03     CR, ETX
```

This explicitly homes the carriage and then enters native OkiGraph data state,
matching the hardware-good behavior developed for the Apple II Print Shop
OkiGraph driver.

### 2. Programmable movement

Stock ML84 descriptor expresses movement as:

```text
ESC % 9 <n> LF
```

R1 redefines the descriptor fields as:

```text
prefix: 03 03
value:  <n>       (spec $81, unchanged)
suffix: 03 02
```

For PSGS's normal seven-dot raster-band request, `n = $0E`, so the emitted
stream is:

```text
03 03 0E 03 02
```

Starting in text state this is interpreted by OkiGraph I as:

```text
03          enter graphics
03 0E       native graphics feed + carriage return
03 02       exit graphics
```

The physical printer therefore supplies the already measured **15/144-inch**
native band movement; we do not substitute ML92/93 movement semantics.

## Unchanged OkiGraph-compatible fields

R1 intentionally retains:

```text
pins:             7
horizontal pitch: 60 columns/inch
logical Y field:  72 (for this protocol test)
graphics end:     03 02
literal ETX:      03 -> 03 03
encoder:          2
```

No byte in `MF`, `SETMAKE`, `INTDRIVERS`, or the ProGrappler interface code is
changed.

## R1 exact descriptor replacement

Stock command segment:

```text
03 1B 25 39 81 01 0A
```

R1:

```text
02 03 03 81 02 03 02
```

Stock graphics begin:

```text
02 1E 03
```

R1:

```text
02 0D 03
```

The record remains exactly 34 bytes and stays at `$0782`; no descriptor table
or subsequent data moves.

## Integrity / hashes

Original PRDRIVERS:

```text
09e51f041e67fa58756c0c32a362bcff7119488af5070df884f4778fff86e3e0
```

R1 PRDRIVERS:

```text
23bddae81c18519c0d2d6c1c6d664088c7b7ea3c5720a054b1e72e2397b7b7fb
```

Exactly **18 bytes** differ in each complete R1 disk image.  The patcher
reopens the resulting ProDOS filesystem, re-extracts PRDRIVERS, reparses the
record, models the `$0E` band movement, and fails if any disk byte outside the
expected PRDRIVERS modifications changes.

R1 main floppy image:

```text
e53d4e67c72c755eaf9522020ed1030773d93de077c1e32bc29bdc26a8712d69
```

R1 v1.1 HD-install image:

```text
2d5e5dd9a1d1e01c86828919666ee624bb5e5df4d34eff9b5d4f6f278bf122c2
```

## Expected hardware result

R1 is a protocol/banding test, not yet the final geometry driver.

The first question is whether the Christmas-card raster now remains coherent
across many bands instead of producing a text-wide line feed followed by
patterned garbage.

If it does, vertical size can still be about `15/14 = 1.071428...`, roughly
7.14% tall, because PSGS is still laying out a conventional seven-dot/72-dpi
logical raster while OkiGraph I physically advances each band origin by
15/144 inch.  Correct nonuniform vertical resampling is a later step after
native protocol stability is proven.

Also intentionally **not fixed in R1**: PSGS Test Paper Position still advances
the paper after printing the reference dots.
