# Current Mirror Design Notes

## 2026-07-01 Initial Template

Added a minimal NMOS current mirror/current sink template to prove the analog
agent stack is not only an OTA-specific flow.

Verification command:

```bash
source env.sh
make eval-current-mirror
```

The block uses `scripts/evaluate_single.py` to run one operating-point
testbench, parse ngspice `.measure` values, compare them against
`specs/current_mirror.yaml`, and write
`circuits/current_mirror/reports/latest_eval.md`.

Measured result:

- `iout_a`: `10.9545 uA`
- `mirror_error`: `9.545%`
- `vref_v`: `0.639369 V`
- `power_w`: `18 uW`

All current mirror template targets pass.
