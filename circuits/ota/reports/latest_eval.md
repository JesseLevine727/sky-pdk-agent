# OTA Evaluation

- Spec: `specs/ota.yaml`
- Template: `circuits/ota/testbenches/ota_ac.spice.in`
- Run root: `circuits/ota/sim/runs/eval`
- Plot: `circuits/ota/sim/runs/eval/metrics.svg`
- Overall: PASS

| Case | Result | Gain dB | UGB Hz | PM deg | Power W | Run Dir |
| --- | :---: | ---: | ---: | ---: | ---: | --- |
| nominal_tt_27c_1v8 | pass | 42.4015 | 1.25546e+07 | 84.653 | 2.95598e-05 | `circuits/ota/sim/runs/eval/nominal_tt_27c_1v8` |
| slow_ss_85c_1v62 | pass | 40.3723 | 1.06653e+07 | 84.9674 | 2.60238e-05 | `circuits/ota/sim/runs/eval/slow_ss_85c_1v62` |
| fast_ff_m40c_1v98 | pass | 43.2266 | 1.31038e+07 | 84.6287 | 2.80617e-05 | `circuits/ota/sim/runs/eval/fast_ff_m40c_1v98` |
| heavy_load_tt_27c_1v8 | pass | 42.4015 | 5.07894e+06 | 88.0731 | 2.95598e-05 | `circuits/ota/sim/runs/eval/heavy_load_tt_27c_1v8` |

## Next Agent Moves

1. Inspect any failing case run directory before changing sizing.
2. Use `make sweep-ota-quick` for a bounded search if failures are coupled.
3. Commit and push after each verified flow improvement or durable design update.
