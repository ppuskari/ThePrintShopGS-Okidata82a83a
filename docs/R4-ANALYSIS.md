# R4 analysis — safe native OkiGraph movement

R4 fixes a protocol mistake in R1/R2/R3.

PSGS passes a **vertical distance** to its generic programmable-spacing routine. R2 inserted that distance directly after an OkiGraph ETX command prefix. That works only when the distance happens to be `$0E`, because `$0E` is OkiGraph I's fixed native graphics feed+CR command.

So R2 could emit invalid streams such as:

```text
03 03 01 03 02
03 03 07 03 02
03 03 15 03 02
```

Those do **not** mean "move 1/7/21 units"; they place arbitrary bytes into OkiGraph command state. This fits the hardware symptoms: the accidental disappearance of the old alignment LF, extra startup graphics, overprint around `Welcome`, and odd back-and-forth carriage motion.

## R4 changes

R4 starts from R2, not R3.

Descriptor:

```text
max movement: $3F -> $0E
```

MF vertical movement at `$75CA`:

```text
R2: 90 10   BCC $75DC   ; emit sub-$0E remainder as a value
R4: 90 3C   BCC $7608   ; existing RTS: suppress remainder
```

PSGS's existing chunk loop then maps movement as:

```text
0..13   -> 0 native feeds
14      -> 1 native feed
15..27  -> 1 native feed, remainder suppressed
28      -> 2 native feeds
N       -> floor(N/14) native feeds
```

Every full chunk still emits exactly:

```text
03 03 0E 03 02
```

Starting in text state:

```text
03        enter graphics
03 0E     native graphics LF + CR
03 02     exit graphics
```

All other R2 protocol behavior remains unchanged: graphics begin `03`, literal raster `03 -> 03 03`, graphics exit `03 02`, PSGS encoder 2, and 60-column/inch horizontal conversion.

## Why Test Paper Position stayed put

The traced alignment path requests movement `$01`. R2 accidentally turned that into command byte `$01`. R4 suppresses it cleanly because it is smaller than one native OkiGraph band. So the useful no-large-linefeed behavior should remain, but now for an intentional reason rather than because of an undefined command.

## Scope and hashes

Compared with R2, R4 changes exactly **two bytes**: one in `PRDRIVERS` and one in `MF`.

```text
MF.R4
bc2f9beac87b9d32f839a5bfd3af8271b42d05649c6ec641a103c4dda875bad9

PRDRIVERS.R4
e535b0eae5c9b5e0fd54cc192369d7dba323254ee3a4f8b702ed65e9e49017b0

Main R4
39658f45eb29440b0d360da9d0508c65019759507848057a083b81f774a57217

HD-install R4
670bad888ac6e8958e08df798c8ffd6315b4e01ade7c6de3ac89cdeb58eaee61
```

Final 15/144-inch vertical page resampling is intentionally postponed.
