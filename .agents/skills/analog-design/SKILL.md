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
6. Run `make eval-ota` when schematic behavior needs named process, voltage, temperature, or load coverage.
7. If one target misses, use `scripts/propose_sizing.py` for a local proposal.
8. If multiple evaluation cases trade off, run `make agent-ota` and inspect `circuits/ota/reports/agent_loop.md`.
9. If a passing recursive candidate exists, apply it with `make agent-ota-apply`; otherwise broaden the candidate axes or escalate topology.
10. If tradeoffs need a broader one-metric sweep, run `scripts/sweep_ota.py` and inspect `ranked_results.json`.
11. If schematic winners may trade off against parasitics, run `make search-ota-postlayout-quick` and inspect `circuits/ota/reports/search_postlayout_summary.md`.
12. Apply the least aggressive passing candidate to the source spec, then rerun the canonical Make target and `make eval-ota`.
13. Record durable design evidence in `circuits/<block>/reports/design_notes.md`.
14. Commit and push after each coherent verified milestone in long-running agent work.
15. Move to Xschem, layout, DRC, LVS, and PEX only after schematic simulation has evidence.
16. For OTA physical work, run `make layout-ota`, `make drc-ota`, `make lvs-ota`, `make pex-ota`, and `make postlayout-ota` in order.
17. Prefer `make signoff-ota` for complete OTA closure evidence.
18. Treat DRC/LVS failures as flow or layout blockers and post-layout target misses as design misses unless the simulator run itself failed.

## Commands

Render OTA netlist:

```bash
make render-ota
```

Run OTA simulation:

```bash
make sim-ota
```

Evaluate OTA across named cases:

```bash
make eval-ota
```

Use a hard evaluation gate:

```bash
make eval-ota-strict
```

Run the bounded recursive agent loop:

```bash
make agent-ota
```

Apply only the best passing recursive candidate:

```bash
make agent-ota-apply
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

Run configured schematic candidate search:

```bash
make search-ota
```

Run configured search with isolated post-layout signoff for top candidates:

```bash
make search-ota-postlayout-quick
```

Generate deterministic OTA Magic layout:

```bash
make layout-ota
```

Run Magic DRC:

```bash
make drc-ota
```

Run Netgen LVS:

```bash
make lvs-ota
```

Run Magic PEX:

```bash
make pex-ota
```

Evaluate the extracted post-layout netlist:

```bash
make postlayout-ota
```

Run complete OTA signoff from the spec flow metadata:

```bash
make signoff-ota
```

Validate repo scripts and this skill:

```bash
make check
```

## Reporting Rules

- State the exact command that produced any result.
- Include the path to the run directory and `measures.json`.
- For sweeps, report the top ranked candidate, whether it passed, and the chosen overrides.
- For evaluations, report the pass/fail count, failing cases, and `circuits/ota/reports/latest_eval.md`.
- For recursive agent loops, report the baseline score, best candidate, whether it was applied, and `circuits/ota/reports/agent_loop.md`.
- For candidate search, report whether ranking used schematic-only or post-layout evidence and cite `circuits/ota/reports/search_summary.md` or `circuits/ota/reports/search_postlayout_summary.md`.
- For signoff orchestration, report each stage result and `circuits/ota/reports/signoff_summary.md`.
- For DRC, report the exact DRC error count and `circuits/ota/reports/drc/drc.md`.
- For LVS, report whether Netgen printed `Netlists match uniquely` and cite `circuits/ota/reports/lvs_ota.md`.
- For PEX, report the extracted netlist path under `circuits/ota/layout/extracted/`.
- For post-layout eval, report pass/fail count, failing cases, and `circuits/ota/reports/postlayout_eval.md`.
- Mark missing EDA tools or missing `PDK_ROOT` as blockers, not design failures.
- Keep proposed changes as spec updates or explicit `--set` overrides.
- Do not edit generated files under `circuits/**/sim/runs/` as source of truth.
- Push after verified milestones when the user has requested periodic remote progress.
