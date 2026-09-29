# R9 — exact 14/15 vertical geometry correction

R9 freezes the hardware-good R8 protocol/state path and changes only vertical source scaling.

Print Shop GS already contains a phase-table vertical resampler. R9 expresses the OkiGraph mechanical correction as the exact integer ratio `70/75 = 14/15`: the private Oki descriptor vertical value changes `72 -> 70`, and the two vertical table-generation bases in MF change `72 -> 75`.

The resulting PSGS phase pattern is `1 1 1 1 1 1 1 0 1 1 1 1 1 1 1`, i.e. fourteen emitted vertical rows for every fifteen logical source rows. Native OkiGraph `$03 $0E` 15/144-inch band movement remains unchanged.

R8 -> R9 changes exactly three physical bytes in each disk image.
