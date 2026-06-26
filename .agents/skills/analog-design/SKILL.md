---
name: analog-design
description: File-based analog IC design workflow for SKY130/open-source EDA. Use when Codex is asked to size, simulate, debug, or report analog blocks using specs, SPICE templates, ngspice measures, Xschem netlists, Magic/KLayout DRC, Netgen LVS, Magic PEX, or files under specs/, circuits/, scripts/, and reports/.
---

# Analog Design

## Overview

Use the repo as an analog design workbench. Edit source files, run deterministic EDA tools, parse their outputs, and report exact evidence. Never substitute reasoning for simulator, DRC, LVS, or PEX results.

For background on the repo contract, read `references/sky130-flow.md` when working on a new block or signoff stage.

## Core Loop

1. Read `AGENTS.md`, the relevant `specs/*.yaml`, and the block files under `circuits/<block>/`.
2. Check setup with `python3 scripts/check_tools.py --soft`.
3. Render the SPICE testbench first with `scripts/run_ngspice.py --dry-run`.
4. Run ngspice only after the rendered netlist looks structurally correct.
5. Parse and inspect `measures.json`; compare each measurement against `targets`.
6. If one target misses, use `scripts/propose_sizing.py` for a local proposal.
7. If tradeoffs are coupled, run `scripts/sweep_ota.py` and inspect `ranked_results.json`.
8. Apply the least aggressive passing candidate to the source spec, then rerun the canonical Make target.
9. Record durable design evidence in `circuits/<block>/reports/design_notes.md`.
10. Move to Xschem, layout, DRC, LVS, and PEX only after schematic simulation has evidence.

## Commands

Render OTA netlist:

```bash
make render-ota
```

Run OTA simulation:

```bash
make sim-ota
```

Generate a sizing proposal:

```bash
make propose-ota
```

Run a deterministic sweep:

```bash
make sweep-ota
```

Run a quick bounded sweep:

```bash
make sweep-ota-quick
```

Validate repo scripts and this skill:

```bash
make check
```

## Reporting Rules

- State the exact command that produced any result.
- Include the path to the run directory and `measures.json`.
- For sweeps, report the top ranked candidate, whether it passed, and the chosen overrides.
- Mark missing EDA tools or missing `PDK_ROOT` as blockers, not design failures.
- Keep proposed changes as spec updates or explicit `--set` overrides.
- Do not edit generated files under `circuits/**/sim/runs/` as source of truth.
