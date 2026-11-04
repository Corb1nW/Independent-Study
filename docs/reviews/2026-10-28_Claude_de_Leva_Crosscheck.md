# de Leva (1996) values used in Stage D1: cross-check of readings

Authored by (model): Claude (Phase D builder), 2026-10-28, in response to ChatGPT's review D1-R03 at `0aa4651`.
Status: **provisional** (Corbin, Q46: "Label provisional, proceed"). No value below has been checked against the paper's printed Table 4.

## Readings compared

1. **BMC** (used): `sources/vendor/bmc/BSPfemale_ZdeLeva.txt`, `BSPmale_ZdeLeva.txt` (Duarte, BMClab/BMC, commit `4d0c2a2`). Machine-readable reproduction.
2. **HAS-Motion wiki**: "Adjusted Zatsiorsky-Seluyanov's segment inertia parameters", read 2026-10-28 through a web-page extraction tool. An independent reproduction. Its head and trunk rows use the alternative CERV endpoints (de Leva's "Head 2" and "Trunk 2"); their mass fractions are the same for every endpoint choice, and Stage D1 uses only the mass fractions of those two segments. Its radius columns are headed IXX, IYY, IZZ; IYY equals de Leva's "transverse" column in BMC for every row checked.
3. **PDF machine extraction**: a text extraction of a PDF copy of the paper, read 2026-10-28. Its Table 4 rows are scrambled, so only values that the extraction placed unambiguously are listed.

## Every de Leva value Stage D1 consumes

| Sex | Segment | Quantity | BMC (used) | HAS-Motion wiki | PDF machine extraction | Agree |
|---|---|---|---|---|---|---|
| female | Head | mass fraction | 0.0668 | 0.0668 | 0.0668 | yes |
| female | Trunk | mass fraction | 0.4257 | 0.4257 | 0.4257 | yes |
| female | Upper arm | mass fraction | 0.0255 | 0.0255 | — | yes |
| female | Forearm | mass fraction | 0.0138 | 0.0138 | — | yes |
| female | Hand | mass fraction | 0.0056 | 0.0056 | — | yes |
| female | Thigh | mass fraction | 0.1478 | 0.1478 | 0.1478 | yes |
| female | Shank | mass fraction | 0.0481 | 0.0481 | 0.0481 | yes |
| female | Foot | mass fraction | 0.0129 | 0.0129 | 0.0129 | yes |
| female | Thigh | centre-of-mass fraction | 0.3612 | 0.3612 | — | yes |
| female | Thigh | radius of gyration (transverse column) | 0.364 | 0.364 | — | yes |
| female | Shank | centre-of-mass fraction | 0.4352 | 0.4352 | — | yes |
| female | Shank | radius of gyration (transverse column) | 0.263 | 0.263 | — | yes |
| male | Head | mass fraction | 0.0694 | 0.0694 | 0.0694 | yes |
| male | Trunk | mass fraction | 0.4346 | 0.4346 | 0.4346 | yes |
| male | Upper arm | mass fraction | 0.0271 | 0.0271 | — | yes |
| male | Forearm | mass fraction | 0.0162 | 0.0162 | — | yes |
| male | Hand | mass fraction | 0.0061 | 0.0061 | — | yes |
| male | Thigh | mass fraction | 0.1416 | 0.1416 | 0.1416 | yes |
| male | Shank | mass fraction | 0.0433 | 0.0433 | 0.0433 | yes |
| male | Foot | mass fraction | 0.0137 | 0.0137 | 0.0137 | yes |
| male | Thigh | centre-of-mass fraction | 0.4095 | 0.4095 | — | yes |
| male | Thigh | radius of gyration (transverse column) | 0.329 | 0.329 | — | yes |
| male | Shank | centre-of-mass fraction | 0.4395 | 0.4395 | — | yes |
| male | Shank | radius of gyration (transverse column) | 0.246 | 0.246 | — | yes |

All 24 consumed fractions agree between the two independent reproductions, and the 10 that the PDF extraction placed unambiguously agree with both.

## Reference body sizes

| Body | Value used | Readings |
|---|---|---|
| Female | 61.9 kg, 1.735 m | PDF extraction of the Table 4 caption ("body mass = 61.9 kg, stature = 173.5 m", the unit an extraction or print error); SimTK lab handout "standard female (1735 mm, 61.9 kg)" |
| Male | 73.0 kg, 1.741 m | PDF extraction of the Table 4 caption only ("73.0 kg, 1.741 m"). **Single reading.** |

## What would close this

Someone with access to the paper compares the 24 values and the two captions above with the printed Table 4 and records the result here. Until then, every result that depends on these values is provisional (D-058 Amendment 3).
