# OTA Evaluation

- Spec: `specs/ota.yaml`
- Template: `circuits/ota/testbenches/ota_ac_postlayout.spice.in`
- Run root: `circuits/ota/sim/runs/postlayout_eval`
- Plot: `circuits/ota/sim/runs/postlayout_eval/metrics.svg`
- Overall: PASS

| Case | Result | Gain dB | UGB Hz | PM deg | Power W | Run Dir |
| --- | :---: | ---: | ---: | ---: | ---: | --- |
| nominal_tt_27c_1v8 | pass | 42.6406 | 1.26424e+07 | 84.0301 | 2.96235e-05 | `circuits/ota/sim/runs/postlayout_eval/nominal_tt_27c_1v8` |
| slow_ss_85c_1v62 | pass | 40.0903 | 1.06286e+07 | 84.3965 | 2.60946e-05 | `circuits/ota/sim/runs/postlayout_eval/slow_ss_85c_1v62` |
| fast_ff_m40c_1v98 | pass | 43.8448 | 1.33807e+07 | 83.9819 | 2.81075e-05 | `circuits/ota/sim/runs/postlayout_eval/fast_ff_m40c_1v98` |
| heavy_load_tt_27c_1v8 | pass | 42.6406 | 5.1627e+06 | 87.7764 | 2.96235e-05 | `circuits/ota/sim/runs/postlayout_eval/heavy_load_tt_27c_1v8` |

## Next Agent Moves

1. Inspect any failing case run directory before changing sizing.
2. Use `make sweep-ota-quick` for a bounded search if failures are coupled.
3. Commit and push after each verified flow improvement or durable design update.
