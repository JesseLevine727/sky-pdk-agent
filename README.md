# Sky PDK Analog Agent

This repo is a file-based scaffold for an LLM-assisted analog design loop on
SKY130. Codex edits specs, SPICE templates, testbenches, scripts, layout Tcl,
and reports. Deterministic EDA tools perform simulation and signoff.

The first target is a minimal 5T OTA flow:

1. Install or point to a SKY130 PDK and set `PDK_ROOT`.
2. Render a primitive or OTA SPICE testbench from a spec file.
3. Run ngspice in batch mode.
4. Parse `.measure` output into JSON.
5. Evaluate named corners and load cases with a durable report.
6. Propose sizing changes from measured misses.
7. Sweep proposed candidates with real simulations.
8. Move to Xschem netlisting, Magic/KLayout layout checks, Netgen LVS, and
   Magic PEX when the schematic simulation loop is stable.

## Tooling

Minimum useful commands:

```bash
source env.sh
python3 scripts/check_tools.py
scripts/setup_pdk.sh
make render-ota
make sim-ota
make eval-ota
make eval-current-mirror
make plan-opamp-comparator-chain
make eval-comparator
make signoff-comparator
make eval-opamp-comparator-chain
make agent-ota
make propose-ota
make sweep-ota-quick
make search-ota
make search-ota-postlayout-quick
make layout-ota
make drc-ota
make lvs-ota
make pex-ota
make postlayout-ota
make signoff-ota
```

`make render-ota` works without ngspice. `make sim-ota` requires ngspice and a
valid SKY130 install.

`make eval-ota` runs every named case in `specs/ota.yaml` and writes
`circuits/ota/reports/latest_eval.md`. It is exploratory and exits successfully
when simulations complete, even if a case misses target. `make eval-ota-strict`
returns nonzero on target misses.

`make eval-current-mirror` runs the NMOS current mirror template through the
generic single-testbench evaluator and writes
`circuits/current_mirror/reports/latest_eval.md`.

`make plan-opamp-comparator-chain` turns
`intents/opamp_comparator_chain.yaml` into a durable implementation plan.
`make eval-comparator` verifies the static CMOS comparator transient template.
`make signoff-comparator` runs schematic eval, deterministic Magic layout, DRC,
LVS, PEX, and post-layout transient evaluation for the comparator.
`make eval-opamp-comparator-chain` verifies the hierarchical mixed-signal
chain where the closed OTA drives the comparator input.

`make agent-ota` runs a bounded recursive loop: baseline evaluation, miss
mining, candidate generation, candidate evaluation, ranking, and a durable
report at `circuits/ota/reports/agent_loop.md`. `make agent-ota-apply` only
updates the source spec when the best candidate passes every named case.

`make search-ota` runs the spec-driven candidate axes under `search.profiles`
and ranks schematic candidates. `make search-ota-postlayout-quick` takes the
top schematic candidates through isolated layout, DRC, LVS, PEX, and
post-layout evaluation, then re-ranks using physical evidence.

`make layout-ota` generates a deterministic Magic PCell route seed from
`specs/ota.yaml` and writes
`circuits/ota/layout/magic/ota_5t_layout_manifest.json` with pin, device,
route-net, and generated-file intent. `make drc-ota` writes
`circuits/ota/reports/drc/drc.md`. `make lvs-ota` compares Magic extraction
against
`circuits/ota/schematic/ota_5t.spice` with Netgen. `make pex-ota` writes the
cap-inclusive extracted SPICE used by `make postlayout-ota`.
`make signoff-ota` runs the whole OTA signoff plan through
`scripts/signoff_block.py` and writes `circuits/ota/reports/signoff_summary.md`.

Expected EDA tools:

- `ngspice` for SPICE simulation
- `xschem` for schematic capture and netlisting
- `magic` and `klayout` for layout/DRC workflows
- `netgen` for LVS

## PDK Setup

The easiest path is Ciel:

```bash
export PDK_ROOT="$HOME/.ciel"
export PDK="sky130A"
scripts/setup_pdk.sh
```

If you already have a PDK, point the repo at it:

```bash
export PDK_ROOT=/path/to/pdk-root
export PDK=sky130A
source env.sh
python3 scripts/check_tools.py
```

The expected model file is:

```text
$PDK_ROOT/sky130A/libs.tech/ngspice/sky130.lib.spice
```

## No-Sudo Tool Install

If system packages cannot be installed because sudo requires a password, this
repo can use locally extracted Ubuntu packages under `.tools/apt` with wrappers
in `bin/`. `env.sh` and the Makefile put those wrappers first on `PATH`.

```bash
scripts/install_local_eda_tools.sh
source env.sh
python3 scripts/check_tools.py
```

The local installer also builds a repo-local Magic when the distro package is
too old or missing SKY130 batch support. `bin/magic` prefers
`.tools/local/magic-8.3.668/bin/magic` when it exists, then falls back to a
system or package-extracted Magic.

## Main Files

- `specs/ota.yaml`: 5T OTA requirements, starting sizing, and simulation setup
- `specs/current_mirror.yaml`: NMOS current mirror requirements and sizing
- `specs/comparator.yaml`: static CMOS comparator transient requirements
- `specs/opamp_comparator_chain.yaml`: hierarchical OTA-to-comparator chain
  requirements
- `specs/primitive_nmos.yaml`: NMOS ID/VGS characterization example
- `intents/opamp_comparator_chain.yaml`: natural-language-style mixed-signal
  design intake file
- `circuits/current_mirror/testbenches/current_mirror_dc.spice.in`: current
  mirror operating-point testbench
- `circuits/comparator/testbenches/comparator_tran.spice.in`: static
  comparator transient testbench
- `circuits/comparator/testbenches/comparator_tran_postlayout.spice.in`:
  extracted-layout static comparator transient testbench
- `circuits/opamp_comparator_chain/testbenches/chain_tran.spice.in`:
  hierarchical OTA/comparator transient testbench
- `circuits/ota/testbenches/ota_ac.spice.in`: OTA AC/DC testbench template
- `circuits/ota/testbenches/ota_ac_postlayout.spice.in`: extracted-layout OTA
  AC/DC testbench template
- `circuits/ota/layout/magic/ota_5t_layout_manifest.json`: deterministic OTA
  layout intent generated beside the Magic Tcl seed
- `scripts/run_ngspice.py`: render, run, and parse one SPICE job
- `scripts/design_intake.py`: convert a design intent YAML file into a
  deterministic scaffold plan
- `scripts/render_comparator_cell.py`: generate the static comparator
  schematic source from `specs/comparator.yaml`
- `scripts/generate_comparator_magic_layout.py`: generate the deterministic
  static comparator Magic layout seed and manifest
- `scripts/evaluate_ota.py`: run named OTA evaluation cases and write a report
- `scripts/evaluate_single.py`: run one testbench, score targets, and write a
  report for simpler blocks
- `scripts/agent_loop.py`: run the recursive Codex-style sizing loop
- `scripts/search_candidates.py`: run spec-driven schematic and post-layout
  candidate search
- `scripts/signoff_block.py`: run reusable schematic/layout/DRC/LVS/PEX
  signoff stages from a block spec
- `scripts/propose_sizing.py`: generate sizing changes from measured misses
- `scripts/sweep_ota.py`: run and rank candidate sweeps using the simulation runner
- `scripts/generate_ota_magic_layout.py`: generate the deterministic Magic
  layout seed from the OTA spec
- `scripts/run_magic_drc.sh`: run Magic DRC and write a durable Markdown report
- `scripts/run_magic_extract_lvs.sh`: create the device-focused extraction used
  for Netgen LVS
- `scripts/run_magic_pex.sh`: create the cap-inclusive extracted SPICE netlist
- `scripts/run_netgen_lvs.sh`: compare schematic and extracted layout netlists
- `AGENTS.md`: repo rules for future Codex sessions
- `.agents/skills/analog-design/SKILL.md`: repo-scoped analog workflow skill
