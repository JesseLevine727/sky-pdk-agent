# Opamp-to-Comparator Chain Design Notes

## 2026-07-01 Mixed-Signal Chain Template

Added a hierarchical transient testbench that instantiates the closed 5T OTA as
an opamp front end and a static CMOS comparator as the decision stage.

Verification commands:

```bash
source env.sh
make plan-opamp-comparator-chain
make eval-comparator
make eval-opamp-comparator-chain
```

Result:

- Intake plan: `circuits/opamp_comparator_chain/reports/design_plan.md`
- Comparator eval: PASS
- Chain eval: PASS
- `amp_initial_v`: `0.3466185`
- `amp_final_v`: `1.414528`
- `amp_cross_time_s`: `1.950965e-08`
- `dout_initial_v`: `1.799997`
- `dout_final_v`: `0.0001339365`
- `decision_delay_s`: `1.911959e-08`
- `power_w`: `3.11317e-05`

The first chain attempt also sampled the final output after the sensor pulse
returned low. Moving `measure_final_time_s` inside the high-input interval
aligned the check with the intended threshold-crossing event. The resulting
testbench now provides a concrete mixed-signal orchestration pattern:
block-level comparator eval, integrated opamp/comparator eval, parsed
measurements, target scoring, and durable reports.
