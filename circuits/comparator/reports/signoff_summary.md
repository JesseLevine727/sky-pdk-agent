# Block Signoff Summary

- Spec: `specs/comparator.yaml`
- Overall: PASS

| Stage | Result | Evidence | Command |
| --- | :---: | --- | --- |
| schematic | pass | `circuits/comparator/schematic/static_comparator.spice` | `/usr/bin/python3 scripts/render_comparator_cell.py --spec specs/comparator.yaml --out circuits/comparator/schematic/static_comparator.spice` |
| schematic-eval | pass | `circuits/comparator/reports/latest_eval.md`, `circuits/comparator/sim/runs/signoff_eval/evaluation.json` | `/usr/bin/python3 scripts/evaluate_single.py --spec specs/comparator.yaml --template circuits/comparator/testbenches/comparator_tran.spice.in --out-dir circuits/comparator/sim/runs/signoff_eval --report circuits/comparator/reports/latest_eval.md --strict` |
| layout | pass | `circuits/comparator/layout/magic/static_comparator.mag` | `/usr/bin/python3 scripts/generate_comparator_magic_layout.py --spec specs/comparator.yaml --out-dir circuits/comparator/layout/magic --run` |
| drc | pass | `circuits/comparator/reports/drc/drc.md` | `scripts/run_magic_drc.sh circuits/comparator/layout/magic/static_comparator.mag circuits/comparator/reports/drc` |
| extract-lvs | pass | `circuits/comparator/layout/extracted/static_comparator_lvs.spice` | `scripts/run_magic_extract_lvs.sh circuits/comparator/layout/magic/static_comparator.mag static_comparator circuits/comparator/layout/extracted/static_comparator_lvs.spice` |
| lvs | pass | `circuits/comparator/reports/lvs_comparator.md` | `scripts/run_netgen_lvs.sh circuits/comparator/layout/extracted/static_comparator_lvs.spice circuits/comparator/schematic/static_comparator.spice static_comparator circuits/comparator/reports/lvs_comparator.md` |
| pex | pass | `circuits/comparator/layout/extracted/static_comparator_extracted.spice` | `scripts/run_magic_pex.sh circuits/comparator/layout/magic/static_comparator.mag static_comparator circuits/comparator/layout/extracted/static_comparator_extracted.spice` |
| postlayout-eval | pass | `circuits/comparator/reports/postlayout_eval.md`, `circuits/comparator/sim/runs/signoff_postlayout_eval/evaluation.json` | `/usr/bin/python3 scripts/evaluate_single.py --spec specs/comparator.yaml --template circuits/comparator/testbenches/comparator_tran_postlayout.spice.in --out-dir circuits/comparator/sim/runs/signoff_postlayout_eval --report circuits/comparator/reports/postlayout_eval.md --strict` |
