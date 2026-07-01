# Block Signoff Summary

- Spec: `specs/ota.yaml`
- Overall: PASS

| Stage | Result | Evidence | Command |
| --- | :---: | --- | --- |
| schematic | pass | `circuits/ota/schematic/ota_5t.spice` | `/usr/bin/python3 scripts/render_ota_cell.py --spec specs/ota.yaml --out circuits/ota/schematic/ota_5t.spice` |
| schematic-eval | pass | `circuits/ota/reports/latest_eval.md`, `circuits/ota/sim/runs/signoff_eval/evaluation.json` | `/usr/bin/python3 scripts/evaluate_ota.py --spec specs/ota.yaml --template circuits/ota/testbenches/ota_ac.spice.in --out-dir circuits/ota/sim/runs/signoff_eval --report circuits/ota/reports/latest_eval.md --strict` |
| layout | pass | `circuits/ota/layout/magic/ota_5t.mag` | `/usr/bin/python3 scripts/generate_ota_magic_layout.py --spec specs/ota.yaml --out-dir circuits/ota/layout/magic --run` |
| drc | pass | `circuits/ota/reports/drc/drc.md` | `scripts/run_magic_drc.sh circuits/ota/layout/magic/ota_5t.mag circuits/ota/reports/drc` |
| extract-lvs | pass | `circuits/ota/layout/extracted/ota_5t_lvs.spice` | `scripts/run_magic_extract_lvs.sh circuits/ota/layout/magic/ota_5t.mag ota_5t circuits/ota/layout/extracted/ota_5t_lvs.spice` |
| lvs | pass | `circuits/ota/reports/lvs_ota.md` | `scripts/run_netgen_lvs.sh circuits/ota/layout/extracted/ota_5t_lvs.spice circuits/ota/schematic/ota_5t.spice ota_5t circuits/ota/reports/lvs_ota.md` |
| pex | pass | `circuits/ota/layout/extracted/ota_5t_extracted.spice` | `scripts/run_magic_pex.sh circuits/ota/layout/magic/ota_5t.mag ota_5t circuits/ota/layout/extracted/ota_5t_extracted.spice` |
| postlayout-eval | pass | `circuits/ota/reports/postlayout_eval.md`, `circuits/ota/sim/runs/signoff_postlayout_eval/evaluation.json` | `/usr/bin/python3 scripts/evaluate_ota.py --spec specs/ota.yaml --template circuits/ota/testbenches/ota_ac_postlayout.spice.in --out-dir circuits/ota/sim/runs/signoff_postlayout_eval --report circuits/ota/reports/postlayout_eval.md --strict` |
