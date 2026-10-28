# Copied source files

Unmodified copies of open source files the data is read from, kept so that a test can show every stored value matches its source (D-058 Amendment 2). Do not edit these files. To update one, copy the new version, record its commit and hash here, and regenerate the datasets with `python -m tools.build_segment_datasets`.

| File | Origin | Commit | SHA-256 | License |
|---|---|---|---|---|
| `opensim-models/gait2392_millard2012muscle.osim` | [opensim-org/opensim-models](https://github.com/opensim-org/opensim-models), `Models/Gait2392_Simbody/gait2392_millard2012muscle.osim` | `d9b05d470b1a481c222372c85b75772faf8f7792` | `9c28e8043cde59bb1354342d6f3ce0ca6a0ea416f08695c0db5387e46a8d464c` | CC BY 3.0, as stated in the file's `<credits>`: Delp, Loan, Hoy, Zajac, Topp, Rosen, Thelen, Anderson, Seth |
| `bmc/BSPfemale_ZdeLeva.txt` | [BMClab/BMC](https://github.com/BMClab/BMC), `data/BSPfemale_ZdeLeva.txt` (Marcos Duarte, *Notes on Scientific Computing for Biomechanics and Motor Control*) | `4d0c2a2ae8adaea578d499076a0c520b2e47d82c` | `83e54e3ef20a6d2475f4629df4e8b2f264090a475870a892ee9abe13d7737699` | CC BY 4.0 (repository `LICENSE.txt`) |
| `bmc/BSPmale_ZdeLeva.txt` | same repository, `data/BSPmale_ZdeLeva.txt` | `4d0c2a2ae8adaea578d499076a0c520b2e47d82c` | `7b1fea6dfd4b79f6b19cce3b2ec36117f00c1c6a0687e42a16848811b3189d2c` | CC BY 4.0 |

The BMC files reproduce de Leva (1996) Table 4 (fractions of body mass and of segment length). They are a secondary source: the values were not checked against the paper itself.
