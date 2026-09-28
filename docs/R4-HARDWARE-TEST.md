# R4 hardware test

Use the same `82A83A OGI` + ProGrappler setup.

First repeat **Test Paper Position / printer test** and note separately whether these are gone, changed, identical, or worse:

- the small blip before the first top-pin alignment dots;
- the roughly four-column block over the beginning of the W in `Welcome`;
- the odd back-and-forth / apparent partial double-printing.

The old large post-dot line feed should remain absent because the traced `$01` movement is now intentionally suppressed.

Then print the **same Christmas card** and inspect the first upper-left panel for the tiny leading blip, the `!`-looking artifact on the final affected band, and the one-column right shift that follows them.

Do not judge final page height yet. R4 still uses native OkiGraph `03 0E`, physically 15/144 inch per band; final vertical resampling comes later.

If the printer-test mechanics clean up but the isolated first-column artifacts remain, keep R4 as the protocol baseline and trace only graphics-run startup next.
