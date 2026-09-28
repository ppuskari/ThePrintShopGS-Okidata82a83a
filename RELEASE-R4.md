# R4 — native movement quantizer

R4 corrects a protocol error in R1/R2/R3: PSGS programmable vertical distances were being inserted as OkiGraph command bytes.

Changes from R2:

- Oki descriptor max movement: `$3F -> $0E`
- `MF:$75CA` BCC displacement: `$10 -> $3C`, so remainders smaller than `$0E` return through the existing `RTS` at `$7608`
- R3 reducer-reset experiment is not carried forward

Result: PSGS movement is quantized to repeated fixed native OkiGraph `$03 $0E` feeds; arbitrary command values are no longer emitted.

This remains a hardware-test build; final nonuniform vertical scaling is still pending.
