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

## 2026-06-26 Recursive Agent Loop

Added `make agent-ota` around `scripts/agent_loop.py`.

Verification command:

```bash
source env.sh
make agent-ota
```

Result:

- Baseline eval score: 2 passing cases, 2 failing cases, total normalized miss
  `0.24058`.
- Best ranked candidate: 3 passing cases, 1 failing case, total normalized miss
  `0.002701`.
- Best candidate overrides:
  - `bias_tail_v=0.7`
  - `devices.mn_in.l_um=1.05`
  - `devices.mn_in.w_um=15.12`
  - `devices.mp_load.l_um=1.05`

The loop did not apply the best candidate because it did not pass every named
evaluation case. This is the intended guardrail: Codex may rank and report
near-misses, but source sizing changes should only be applied automatically when
the deterministic eval gate passes.

## 2026-06-26 Strict Evaluation Closure

Closed the remaining schematic-level eval blockers with a refined sizing point:

- `bias_tail_v=0.70`
- `devices.mn_in.w_um=15.12`
- `devices.mn_in.l_um=1.05`
- `devices.mp_load.w_um=22`
- `devices.mp_load.l_um=1.05`

Verification command:

```bash
source env.sh
make eval-ota-strict
```

Measured result:

- `nominal_tt_27c_1v8`: gain `42.3525 dB`, UGB `12.5808 MHz`,
  phase margin `85.1619 deg`, power `29.5592 uW`
- `slow_ss_85c_1v62`: gain `40.174 dB`, UGB `10.6827 MHz`,
  phase margin `85.4607 deg`, power `26.0232 uW`
- `fast_ff_m40c_1v98`: gain `43.2292 dB`, UGB `13.132 MHz`,
  phase margin `85.139 deg`, power `28.0614 uW`
- `heavy_load_tt_27c_1v8`: gain `42.3525 dB`, UGB `5.08037 MHz`,
  phase margin `88.2901 deg`, power `29.5592 uW`

All named schematic-level evaluation cases now pass the current targets.

## 2026-06-26 Schematic Source Netlist

Added a committed schematic-level source cell at
`circuits/ota/schematic/ota_5t.spice`, generated from `specs/ota.yaml` by
`make netlist-ota`. The AC testbench now includes and instantiates this cell
instead of embedding transistor instances directly in the testbench.

Verification commands:

```bash
source env.sh
make sim-ota
make eval-ota-strict
```

Result:

- `make sim-ota` passed and wrote
  `circuits/ota/sim/runs/latest/measures.json`.
- `make eval-ota-strict` passed all 4 named cases with the included
  `ota_5t` subcircuit.

This gives the flow a stable schematic SPICE boundary for later LVS and PEX
comparison while preserving `--set` overrides through subcircuit parameters.

## 2026-06-26 Physical Flow Closure

Added a deterministic Magic layout seed, DRC, LVS extraction, PEX extraction,
and post-layout OTA evaluation path.

Verification commands:

```bash
source env.sh
make drc-ota
make lvs-ota
make pex-ota
make postlayout-ota
```

Physical signoff evidence:

- `make drc-ota` wrote `circuits/ota/reports/drc/drc.md` with 0 Magic DRC
  errors.
- `make lvs-ota` wrote `circuits/ota/reports/lvs_ota.md` with 5 devices on
  both sides, 8 nets on both sides, and `Netlists match uniquely`.
- `make pex-ota` wrote
  `circuits/ota/layout/extracted/ota_5t_extracted.spice`.
- `make postlayout-ota` wrote `circuits/ota/reports/postlayout_eval.md`.

Post-layout result:

- `nominal_tt_27c_1v8`: pass, gain `42.5724 dB`, UGB `12.6845 MHz`,
  phase margin `84.5563 deg`, power `29.6231 uW`
- `slow_ss_85c_1v62`: fail, gain `39.8391 dB`, UGB `10.6581 MHz`,
  phase margin `84.9065 deg`, power `26.094 uW`
- `fast_ff_m40c_1v98`: pass, gain `43.841 dB`, UGB `13.4265 MHz`,
  phase margin `84.517 deg`, power `28.1073 uW`
- `heavy_load_tt_27c_1v8`: pass, gain `42.5724 dB`, UGB `5.16631 MHz`,
  phase margin `88.0088 deg`, power `29.6231 uW`

At this milestone the remaining extracted-layout miss was small but real:
`slow_ss_85c_1v62` missed the 40 dB gain target by about 0.004 dB. Trial
nudges to PMOS load length, NMOS input width, and tail bias either worsened the
post-layout slow gain or broke schematic strict evaluation, so the initial
physical-flow state preserved the schematic-closed baseline and recorded the
post-layout miss explicitly.

## 2026-06-26 Post-Layout Closure

Closed the extracted-layout slow-corner gain miss by increasing the PMOS
current-mirror load width:

- `devices.mp_load.w_um`: `22` -> `26`

Focused candidate screen:

- Lowering `bias_tail_v` to `0.68` or `0.69` fixed slow gain but dropped
  heavy-load UGB below 5 MHz.
- Increasing `devices.mn_in.l_um` improved slow gain but did not reach 40 dB.
- Increasing `devices.mp_load.w_um` to `26` passed the extracted slow-corner
  gain screen and preserved heavy-load UGB.

Verification command:

```bash
source env.sh
make check
make eval-ota-strict
make drc-ota
make lvs-ota
make pex-ota
make postlayout-ota
```

Schematic eval result:

- `nominal_tt_27c_1v8`: gain `42.4015 dB`, UGB `12.5546 MHz`,
  phase margin `84.653 deg`, power `29.5598 uW`
- `slow_ss_85c_1v62`: gain `40.3723 dB`, UGB `10.6653 MHz`,
  phase margin `84.9674 deg`, power `26.0238 uW`
- `fast_ff_m40c_1v98`: gain `43.2266 dB`, UGB `13.1038 MHz`,
  phase margin `84.6287 deg`, power `28.0617 uW`
- `heavy_load_tt_27c_1v8`: gain `42.4015 dB`, UGB `5.07894 MHz`,
  phase margin `88.0731 deg`, power `29.5598 uW`

Post-layout eval result:

- `nominal_tt_27c_1v8`: gain `42.6406 dB`, UGB `12.6424 MHz`,
  phase margin `84.0301 deg`, power `29.6235 uW`
- `slow_ss_85c_1v62`: gain `40.0903 dB`, UGB `10.6286 MHz`,
  phase margin `84.3965 deg`, power `26.0946 uW`
- `fast_ff_m40c_1v98`: gain `43.8448 dB`, UGB `13.3807 MHz`,
  phase margin `83.9819 deg`, power `28.1075 uW`
- `heavy_load_tt_27c_1v8`: gain `42.6406 dB`, UGB `5.1627 MHz`,
  phase margin `87.7764 deg`, power `29.6235 uW`

Physical gates:

- Magic DRC: 0 errors.
- Netgen LVS: `Netlists match uniquely`.
- Magic PEX: wrote `circuits/ota/layout/extracted/ota_5t_extracted.spice`.

All named schematic and extracted-layout evaluation cases now pass the current
targets.

## 2026-07-01 Search and Signoff Generalization

Added a reusable signoff orchestrator and spec-driven candidate search:

- `scripts/signoff_block.py` runs the OTA stage plan from `specs/ota.yaml`
  flow metadata and writes `circuits/ota/reports/signoff_summary.md`.
- `scripts/search_candidates.py` reads `search.profiles` from the spec, ranks
  schematic candidates, and can send top candidates through isolated
  layout/DRC/LVS/PEX/post-layout signoff directories.

Verification commands:

```bash
source env.sh
make check
make signoff-ota
make search-ota
make search-ota-postlayout-quick
```

Result:

- `make signoff-ota` passed all 8 stages.
- `make search-ota` ranked `devices.mp_load.w_um=24` first using schematic
  evidence only.
- `make search-ota-postlayout-quick` re-ranked candidates with physical
  evidence: `devices.mp_load.w_um=24` passed schematic but failed post-layout,
  while `devices.mp_load.w_um=26` passed schematic and post-layout and ranked
  first.

This is the intended agentic analog pattern: schematic search is used as a fast
screen, but source candidates are not treated as closed until layout extraction
and post-layout evaluation agree.
