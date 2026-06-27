# OTA Evaluation

- Spec: `specs/ota.yaml`
- Template: `circuits/ota/testbenches/ota_ac_postlayout.spice.in`
- Run root: `circuits/ota/sim/runs/postlayout_eval`
- Plot: `circuits/ota/sim/runs/postlayout_eval/metrics.svg`
- Overall: FAIL

| Case | Result | Gain dB | UGB Hz | PM deg | Power W | Run Dir |
| --- | :---: | ---: | ---: | ---: | ---: | --- |
| nominal_tt_27c_1v8 | pass | 42.5724 | 1.26845e+07 | 84.5563 | 2.96231e-05 | `circuits/ota/sim/runs/postlayout_eval/nominal_tt_27c_1v8` |
| slow_ss_85c_1v62 | fail | 39.8391 | 1.06581e+07 | 84.9065 | 2.6094e-05 | `circuits/ota/sim/runs/postlayout_eval/slow_ss_85c_1v62` |
| fast_ff_m40c_1v98 | pass | 43.841 | 1.34265e+07 | 84.517 | 2.81073e-05 | `circuits/ota/sim/runs/postlayout_eval/fast_ff_m40c_1v98` |
| heavy_load_tt_27c_1v8 | pass | 42.5724 | 5.16631e+06 | 88.0088 | 2.96231e-05 | `circuits/ota/sim/runs/postlayout_eval/heavy_load_tt_27c_1v8` |

## Failing Cases

- `slow_ss_85c_1v62`: dc_gain_db miss 0.00402125.

## Next Agent Moves

1. Inspect any failing case run directory before changing sizing.
2. Use `make sweep-ota-quick` for a bounded search if failures are coupled.
3. Commit and push after each verified flow improvement or durable design update.
