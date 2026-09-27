# R0 — ML84 descriptor compatibility proof

R0 is the first hardware-validation build for **The Print Shop GS — Okidata 82A/83A OkiGraph I** project.

## Scope

R0 deliberately makes only one logical modification:

```text
Okidata 84  ->  82A83A OGI
```

The strings are equal length. The printer-selection table does not move, the descriptor pointer remains `$0782`, and the original ML84 descriptor remains byte-for-byte unchanged.

## Why

The PSGS ML84 descriptor already matches many independently recovered OkiGraph I characteristics: seven-dot Oki graphics, 60 horizontal graphics columns/inch, programmable Oki spacing, ETX graphics mode, ETX-STX graphics exit, and apparent literal-ETX escaping support.

R0 tests that compatibility directly before adding new behavior.

## Expected imperfection

The main known difference is native vertical movement:

```text
standard Oki 7-bit graphics: 14/144 inch per band
82A/83A OkiGraph I:          15/144 inch per band
```

Therefore a coherent print that is roughly **7.14% too tall** is considered a highly useful R0 result rather than a failure.

## Reproducibility

Use the fail-closed patcher in `scripts/patch_psgs_okigraph_r0.py` against a matching original `.2mg` image.

See `SHA256SUMS-R0.txt` for the known `PRDRIVERS` and initial output hashes.

## Redistributable contents

The repository contains no original or patched Broderbund disk image. R0 is reproduced locally from a user-owned archival image.
