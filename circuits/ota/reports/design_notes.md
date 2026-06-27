# OTA Design Notes

## 2026-06-26 Gain Closure

Starting point:

- `dc_gain_db`: 37.04889 dB
- `unity_gain_hz`: 16.41568 MHz
- `phase_margin_deg`: 88.71514 deg
- `power_w`: 38.18772 uW

Target miss:

- Gain target is `> 40 dB`; the starting point missed by about 2.95 dB.

Agent/design action:

1. Ran a limited gain-oriented sweep with `scripts/sweep_ota.py`.
2. Best 60-candidate sweep result reached 39.59545 dB with:
   - `devices.mn_in.l_um=0.6`
   - `devices.mp_load.l_um=0.6`
   - `devices.mn_in.w_um=10.8`
   - `bias_tail_v=0.68`
3. Ran two manual refinements at `0.7um` and `0.8um` channel length.
4. Chose the less aggressive passing candidate:
   - `devices.mn_in.l_um=0.7`
   - `devices.mp_load.l_um=0.7`
   - `devices.mn_in.w_um=10.8`
   - `bias_tail_v=0.68`

Verification command:

```bash
source env.sh
make sim-ota
```

Final measured result:

- `dc_gain_db`: 40.51683 dB
- `unity_gain_hz`: 9.75349 MHz
- `phase_margin_deg`: 87.85694 deg
- `power_w`: 22.13244 uW

All initial OTA targets pass in TT schematic-level simulation.

## 2026-06-26 Multi-Case Evaluation Harness

Added `make eval-ota` to run named cases from `specs/ota.yaml` and write
`circuits/ota/reports/latest_eval.md`.

Verification command:

```bash
source env.sh
make eval-ota
```

Result:

- Cases run: 4
- Passed: 2
- Failed targets: 2
- Simulator errors: 0

Failing cases:

- `slow_ss_85c_1v62`: gain is 39.0318 dB against the 40 dB target.
- `heavy_load_tt_27c_1v8`: unity-gain bandwidth is 3.91813 MHz against the
  5 MHz target.

The current OTA remains nominal-TT passing. The next design work should close
the slow-corner gain miss and heavy-load bandwidth miss, then rerun
`make eval-ota-strict`.
