# Analog Agent Flow

The repo flow is intentionally file-based.

1. Specs define targets, model paths, operating point, and starting sizes.
2. SPICE templates use `${name}` substitutions from flattened specs.
3. `scripts/run_ngspice.py` renders an effective netlist into a run directory.
4. ngspice runs in batch mode and writes a log.
5. `scripts/parse_measures.py` extracts `.measure` values to JSON.
6. `scripts/design_intake.py` turns a design intent YAML file into a durable
   implementation/scaffold plan.
7. `scripts/evaluate_single.py` runs one-testbench blocks and writes a durable
   target-scored report.
8. `scripts/evaluate_ota.py` runs named cases from the spec, writes
   `evaluation.json`, creates an SVG metric plot, and updates
   `circuits/ota/reports/latest_eval.md`.
9. `scripts/agent_loop.py` runs the recursive agent loop: baseline evaluation,
   miss mining, bounded candidate generation, candidate evaluation, ranking,
   optional safe apply, and report writing.
10. `scripts/propose_sizing.py` compares measurements to spec bounds and writes
   a proposed override set.
11. `scripts/sweep_ota.py` evaluates candidates by calling the same runner and
   writes `ranked_results.json` plus `summary.md` in the sweep run directory.
12. `scripts/search_candidates.py` evaluates spec-configured candidate axes and
    can promote top schematic candidates into isolated physical signoff runs.
13. `scripts/generate_ota_magic_layout.py` creates a deterministic Magic layout
    seed and JSON layout manifest from the same OTA spec.
14. Magic DRC, Netgen LVS, Magic PEX, and post-layout ngspice evaluation run as
    deterministic gates after schematic simulation meets spec.
15. `scripts/signoff_block.py` runs the reusable end-to-end signoff stage plan
    from block spec metadata and writes a durable summary.

This separation is the contract for agent work: Codex may propose and edit
files, but EDA tools produce verification evidence.

## Co-Evolution Rule

When the agent improves a circuit, also improve the loop if the process exposed
a repeated manual step. Examples: add a parser, score candidates, write a
durable report, or update the repo skill with the new workflow rule.

## Full Stack Roadmap

The intended open-source analog stack is:

```text
spec -> topology/sizing -> ngspice eval -> sweep/proposal -> Xschem netlist
     -> Magic/KLayout DRC -> Netgen LVS -> Magic PEX -> post-layout eval
     -> final report
```

Each stage should be file-based: Codex edits specs, netlists, testbenches,
scripts, layout Tcl, measurement code, and reports; deterministic tools produce
the evidence.

## Current Stack Status

- Working: tool checks, primitive sim, OTA nominal sim, multi-case OTA eval,
  current mirror template eval, mixed-signal design intake planning, static
  comparator eval, comparator physical signoff, OTA-to-comparator chain eval,
  recursive candidate ranking, sizing proposal reports, deterministic sweep
  reports, schematic SPICE source generation, deterministic Magic layout seeds
  plus layout manifests, spec-driven schematic search, isolated post-layout
  candidate search, Magic DRC, Netgen LVS, Magic PEX, post-layout evaluation,
  and reusable block signoff orchestration.
- Current schematic OTA result: `make eval-ota-strict` passes all 4 named cases.
- Current physical OTA result: `make drc-ota` reports 0 Magic DRC errors and
  `make lvs-ota` reports `Netlists match uniquely`.
- Current post-layout result: `make postlayout-ota` completes and passes all 4
  named extracted-layout cases.
- Current search result: `make search-ota-postlayout-quick` demonstrates the
  schematic/layout tradeoff directly: `mp_load.w_um=24` passes schematic but
  fails post-layout, while `mp_load.w_um=26` passes both and ranks first after
  physical evidence.
- Current second-template result: `make eval-current-mirror` passes the NMOS
  current mirror one-testbench spec.
- Current mixed-signal result: `make eval-comparator` passes the static CMOS
  comparator transient spec, and `make eval-opamp-comparator-chain` passes the
  hierarchical OTA-to-comparator transient spec.
- Current comparator physical result: `make signoff-comparator` passes all 8
  stages, with 0 Magic DRC errors, `Netlists match uniquely`, and passing
  post-layout transient evaluation.

## Periodic Push Rule

For long-running agentic work, commit and push after each coherent verified
milestone. A good milestone is a passing script/test addition, a durable design
update with simulator evidence, or a completed documentation/rule update.
