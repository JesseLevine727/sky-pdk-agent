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

## 2026-07-01 Physical Signoff Template

Added a spec-driven schematic generator, deterministic Magic layout generator,
layout manifest, DRC/LVS/PEX targets, and post-layout transient evaluation for
the static comparator.

Verification command:

```bash
source env.sh
make signoff-comparator
```

Physical evidence:

- Signoff summary: `circuits/comparator/reports/signoff_summary.md`
- Layout manifest:
  `circuits/comparator/layout/magic/static_comparator_layout_manifest.json`
- Magic DRC: 0 errors in `circuits/comparator/reports/drc/drc.md`
- Netgen LVS: `Netlists match uniquely` in
  `circuits/comparator/reports/lvs_comparator.md`
- PEX netlist:
  `circuits/comparator/layout/extracted/static_comparator_extracted.spice`
- Post-layout eval: PASS in `circuits/comparator/reports/postlayout_eval.md`

Post-layout measured result:

- `delay_s`: `1.270771e-10`
- `vout_initial_v`: `1.8`
- `vout_final_v`: `8.220663e-06`
- `power_w`: `7.18641e-08`

The first physical routing attempts were rejected by LVS because the small
device PCells expose both top and bottom gate contacts and have terminal
coordinates different from the OTA layout approximation. The final generator
uses comparator-specific terminal coordinates and routes drains left, sources
right, and gates on a separate left bus.
