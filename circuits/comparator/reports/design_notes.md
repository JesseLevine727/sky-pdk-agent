# Static Comparator Design Notes

## 2026-07-01 Initial Transient Template

Added a SKY130 static CMOS comparator/inverter threshold detector and a
single-testbench transient evaluation path.

Verification command:

```bash
source env.sh
make eval-comparator
```

Result:

- Overall: PASS
- `delay_s`: `8.204048e-11`
- `vout_initial_v`: `1.8`
- `vout_final_v`: `8.22067e-06`
- `power_w`: `4.03956e-08`

The first attempted measurement sampled the final output after the input pulse
had already returned low. The spec now measures the final state while the input
is still high, so the target check corresponds to the intended high-input
decision interval.
