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
make agent-ota
make propose-ota
make sweep-ota-quick
```

`make render-ota` works without ngspice. `make sim-ota` requires ngspice and a
valid SKY130 install.

`make eval-ota` runs every named case in `specs/ota.yaml` and writes
`circuits/ota/reports/latest_eval.md`. It is exploratory and exits successfully
when simulations complete, even if a case misses target. `make eval-ota-strict`
returns nonzero on target misses.

`make agent-ota` runs a bounded recursive loop: baseline evaluation, miss
mining, candidate generation, candidate evaluation, ranking, and a durable
report at `circuits/ota/reports/agent_loop.md`. `make agent-ota-apply` only
updates the source spec when the best candidate passes every named case.

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

## Main Files

- `specs/ota.yaml`: 5T OTA requirements, starting sizing, and simulation setup
- `specs/primitive_nmos.yaml`: NMOS ID/VGS characterization example
- `circuits/ota/testbenches/ota_ac.spice.in`: OTA AC/DC testbench template
- `scripts/run_ngspice.py`: render, run, and parse one SPICE job
- `scripts/evaluate_ota.py`: run named OTA evaluation cases and write a report
- `scripts/agent_loop.py`: run the recursive Codex-style sizing loop
- `scripts/propose_sizing.py`: generate sizing changes from measured misses
- `scripts/sweep_ota.py`: run and rank candidate sweeps using the simulation runner
- `AGENTS.md`: repo rules for future Codex sessions
- `.agents/skills/analog-design/SKILL.md`: repo-scoped analog workflow skill
