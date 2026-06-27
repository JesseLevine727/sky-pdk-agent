# OTA Agent Loop

- Spec: `specs/ota.yaml`
- Template: `circuits/ota/testbenches/ota_ac.spice.in`
- Run root: `circuits/ota/sim/runs/agent_loop`
- Applied best passing candidate: no

## Baseline

- Pass: `False`
- Passed cases: `2`
- Failed cases: `2`
- Total normalized miss: `0.24058`

## Ranked Candidates

| Rank | Pass | Passed | Failed | Total Miss | Worst Miss | Avg Power W | Overrides |
| ---: | :---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | no | 3 | 1 | 0.002701 | 0.002701 | 2.83001e-05 | `bias_tail_v=0.7, devices.mn_in.l_um=1.05, devices.mn_in.w_um=15.12, devices.mp_load.l_um=1.05` |
| 2 | no | 3 | 1 | 0.0135758 | 0.0135758 | 3.68866e-05 | `bias_tail_v=0.72, devices.mn_in.l_um=1.05, devices.mn_in.w_um=14.04, devices.mp_load.l_um=1.05` |
| 3 | no | 3 | 1 | 0.0236783 | 0.0236783 | 3.6872e-05 | `bias_tail_v=0.72, devices.mn_in.l_um=0.84, devices.mn_in.w_um=12.96, devices.mp_load.l_um=0.84` |
| 4 | no | 3 | 1 | 0.0504362 | 0.0504362 | 5.79659e-05 | `bias_tail_v=0.76, devices.mn_in.l_um=0.77, devices.mn_in.w_um=14.04, devices.mp_load.l_um=0.77` |
| 5 | no | 3 | 1 | 0.21278 | 0.21278 | 2.10407e-05 | `bias_tail_v=0.68, devices.mn_in.l_um=1.05, devices.mn_in.w_um=14.04, devices.mp_load.l_um=1.05` |
| 6 | no | 2 | 2 | 0.0486226 | 0.0462548 | 2.45919e-05 | `bias_tail_v=0.69, devices.mn_in.l_um=1.05, devices.mn_in.w_um=19.98, devices.mp_load.l_um=1.05` |

## Recommendation

No candidate passed every evaluation case. The best candidate improved the score; inspect the ranked table before broadening the search.
Next search axes: gm/ID characterization, separate input/load length sweeps, and topology alternatives if 5T OTA tradeoffs remain too tight.

## Recursive Loop Contract

1. Run preflight checks.
2. Evaluate baseline.
3. Generate bounded candidates from actual target misses.
4. Evaluate candidates with ngspice.
5. Apply only a passing candidate unless explicitly overridden.
6. Re-run `make check` and `make eval-ota-strict` after any applied sizing change.
7. Commit and push each verified milestone.
