# OTA Evaluation

- Spec: `specs/ota.yaml`
- Template: `circuits/ota/testbenches/ota_ac.spice.in`
- Run root: `circuits/ota/sim/runs/eval`
- Plot: `circuits/ota/sim/runs/eval/metrics.svg`
- Overall: FAIL

| Case | Result | Gain dB | UGB Hz | PM deg | Power W | Run Dir |
| --- | :---: | ---: | ---: | ---: | ---: | --- |
| nominal_tt_27c_1v8 | pass | 40.5168 | 9.75349e+06 | 87.8569 | 2.21324e-05 | `circuits/ota/sim/runs/eval/nominal_tt_27c_1v8` |
| slow_ss_85c_1v62 | fail | 39.0318 | 8.57603e+06 | 88.0257 | 2.02336e-05 | `circuits/ota/sim/runs/eval/slow_ss_85c_1v62` |
| fast_ff_m40c_1v98 | pass | 41.0466 | 9.43243e+06 | 87.8868 | 1.94964e-05 | `circuits/ota/sim/runs/eval/fast_ff_m40c_1v98` |
| heavy_load_tt_27c_1v8 | fail | 40.5168 | 3.91813e+06 | 89.4603 | 2.21324e-05 | `circuits/ota/sim/runs/eval/heavy_load_tt_27c_1v8` |

## Failing Cases

- `slow_ss_85c_1v62`: dc_gain_db miss 0.0242062.
- `heavy_load_tt_27c_1v8`: unity_gain_hz miss 0.216373.

## Next Agent Moves

1. Inspect any failing case run directory before changing sizing.
2. Use `make sweep-ota-quick` for a bounded search if failures are coupled.
3. Commit and push after each verified flow improvement or durable design update.
