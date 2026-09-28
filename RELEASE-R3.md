# R3 — horizontal reducer row-reset diagnostic

R3 follows hardware testing of R2, where graphics are coherent but two isolated
bands in the first Christmas-card panel begin with one extra graphics column,
shifting the intended band one column to the right.

## Descriptor trace result

The PSGS Oki graphics-format flag (`1`) selects an **unsized streaming** path.
The graphics begin routine emits only the configured begin string; it does not
transmit a width/count.  The two preceding optional descriptor blocks are
horizontal positioning and color selection, not graphics sizing.

Therefore R3 does not modify any OkiGraph I command field.

## R3 code change

At `MF:$72F9`:

```text
9C 07 73     STZ $7307
```

becomes:

```text
20 25 75     JSR $7525
```

`$7307` has no read references in MF.  Existing helper `$7525` resets:

```text
$73E7  120->60 reducer phase/index
$7869  OR accumulator 1
$786B  OR accumulator 2
```

This makes each raster row start from a known 60-dpi horizontal reduction state.

## Protocol

Identical to R2: native 82A/83A OkiGraph I framing, literal `$03` escaping,
60-column/inch seven-dot encoder, and native 15/144-inch band movement.

## Change scope

Compared with R2: exactly **3 bytes** differ, all in `MF`.

Compared with the original disks: **30 bytes** differ total — 27 R2
`PRDRIVERS` bytes plus the 3-byte R3 MF hook.

This remains a hardware-test build.  Vertical resampling is intentionally
postponed until horizontal band-origin correctness is confirmed.
