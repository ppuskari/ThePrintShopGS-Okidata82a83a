# R2 — ETX-only graphics-entry test

R2 is a surgical follow-up to the first coherent native OkiGraph I build, R1.

R1 proved sustained 82A/83A OkiGraph graphics, correct native band movement, and working PSGS 7-dot raster conversion, but physical output showed a few isolated text-like marks at panel boundaries.

R2 changes only the logical graphics-entry command:

```text
R1: 0D 03     CR, ETX
R2:    03     ETX only
```

The native OkiGraph band movement remains `03 03 <n> 03 02`, literal raster `$03` remains escaped as `03 03`, graphics exit remains `03 02`, and PSGS encoder selector 2 remains unchanged.

No PSGS executable code is modified. The stock ML92/93 entry remains untouched.

Because PSGS descriptors use packed length-prefixed strings, the one-byte-shorter entry field shifts the remaining ML84 descriptor tail left one byte. The unused final byte of the fixed ML84 slot is zero padding; the next descriptor remains at stock pointer `$07A4` and is unchanged.
