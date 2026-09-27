# R0 hardware validation

## Purpose

R0 deliberately reuses the original Print Shop GS **Okidata 84** descriptor unchanged. The only program-data modification is renaming the selector to `82A83A OGI`.

The first hardware test therefore determines whether Broderbund's ML84 path is already wire-compatible with OkiGraph I before we alter any commands or geometry.

## Preferred first printer

Use the **MICROLINE 83A + OkiGraph I** first if convenient.

The ML84 was also a wide-carriage machine. Starting with the 83A reduces the number of variables in the first experiment. Repeat on the 82A after the protocol behavior is understood.

## PSGS setup

1. Boot the R0-patched Print Shop GS disk/install.
2. Open printer/interface Setup.
3. Choose:

   ```text
   82A83A OGI
   ```

4. Select the actual interface/slot configuration normally used with the printer.
5. Allow PSGS to regenerate `PRINTER.DRIVER` from the selected printer descriptor and interface driver.

## First test artwork

Use a simple monochrome design containing:

- a large rectangle;
- at least one known-size 1-inch reference square;
- a solid black region;
- diagonals in both directions;
- long horizontal rules crossing many raster-band boundaries; and
- 4-6 inches of vertical extent so scaling error is easy to measure.

Avoid complicated fonts, color, cards, banners, or stationery in the very first test. We want a clean protocol/geometry result.

## Record independently

### Protocol/state

- Does the printer enter graphics mode?
- Is the output recognizably the intended artwork?
- Does graphics mode remain stable through the whole page?
- Does the printer exit graphics cleanly at end of page?
- Are there random command-like disruptions that could indicate a literal `$03` collision?

### Horizontal behavior

- Is the horizontal scale approximately correct?
- Are successive bands registered at the same left margin?
- Is there cumulative left/right staircase drift?
- Is the output clipped on the right?

### Vertical behavior

Measure a known vertical feature and record both intended and actual height.

The leading R0 hypothesis is:

```text
OkiGraph native band feed = 15/144 inch
standard Oki band model   = 14/144 inch
ratio                     = 15/14
                          = 1.071428...
```

If the ML84 path assumes the standard Oki movement, a coherent R0 image may therefore be about **7.14% too tall** over long spans.

Also note:

- visible white seams between bands;
- overlapping bands;
- skipped/doubled vertical movement; and
- whether vertical error accumulates uniformly.

## What counts as a strong R0 success

A strong R0 result is **not necessarily perfect geometry**.

The most valuable outcome is:

- coherent artwork;
- correct left/right registration;
- stable Oki graphics state;
- correct horizontal scale; and
- a repeatable vertical-only error.

That result would demonstrate that the existing PSGS Oki machinery already solves most of the protocol problem and that R1 can focus primarily on OkiGraph I vertical geometry.

## R1 branches

### Coherent but ~7% tall

Preserve the Oki framing and investigate descriptor-level vertical compensation first.

### Random corruption / unexpected mode changes

Trace the ML84 descriptor's literal-ETX substitution definition and compare it with the hardware-golden OkiGraph I escaping behavior.

### No vertical movement between bands

Patch the band-advance definition toward explicit OkiGraph `ETX $0E` graphics-feed + CR semantics.

### Graphics never starts

Reduce the ML84 graphics-entry sequence from `RS, ETX` to the minimum OkiGraph I `ETX` entry and retest.

### 83A works, 82A clips

Treat printable width/page geometry as a separate issue from the protocol path.
