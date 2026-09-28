# R5 — native OkiGraph movement sanitizer

R5 returns to the coherent R2 baseline. R3's reducer-reset experiment and R4's sub-band suppression are not carried forward.

The remaining protocol problem was that PSGS could insert arbitrary positive movement values into the R2 OkiGraph sequence. Only `$0E` is the proven native graphics feed+CR command.

R5 changes the repurposed OkiGraph descriptor's maximum movement chunk from `$3F` to `$0E` and replaces `MF:$75C7`'s `CMP $7861` with a call to a 27-byte hook in shipped zero padding at `$7E67`. For this unique driver only, positive remainders below `$0E` are rounded up to `$0E`; all stock printers retain original compare semantics.

The existing PSGS chunk loop therefore emits `ceil(distance/14)` copies of the hardware-proven native movement and never sends arbitrary OkiGraph command values.

This is still a hardware-test build. Final vertical resampling/scaling is intentionally postponed.
