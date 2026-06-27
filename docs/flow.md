# Analog Agent Flow

The repo flow is intentionally file-based.

1. Specs define targets, model paths, operating point, and starting sizes.
2. SPICE templates use `${name}` substitutions from flattened specs.
3. `scripts/run_ngspice.py` renders an effective netlist into a run directory.
4. ngspice runs in batch mode and writes a log.
5. `scripts/parse_measures.py` extracts `.measure` values to JSON.
6. `scripts/evaluate_ota.py` runs named cases from the spec, writes
   `evaluation.json`, creates an SVG metric plot, and updates
   `circuits/ota/reports/latest_eval.md`.
7. `scripts/agent_loop.py` runs the recursive agent loop: baseline evaluation,
   miss mining, bounded candidate generation, candidate evaluation, ranking,
   optional safe apply, and report writing.
8. `scripts/propose_sizing.py` compares measurements to spec bounds and writes
   a proposed override set.
9. `scripts/sweep_ota.py` evaluates candidates by calling the same runner and
   writes `ranked_results.json` plus `summary.md` in the sweep run directory.
10. Xschem, Magic, Netgen, and PEX scripts are used after schematic simulation
   meets spec.

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
  recursive candidate ranking, sizing proposal reports, and deterministic
  sweep reports.
- Hooked but not complete: Xschem netlisting, Magic/KLayout DRC, Netgen LVS,
  Magic PEX, and post-layout evaluation.
- Current OTA result: nominal TT passes; the recursive loop improves multi-case
  eval from 2/4 passing to 3/4 passing but has not found a full 4/4 passing
  5T OTA candidate under the current targets.

## Periodic Push Rule

For long-running agentic work, commit and push after each coherent verified
milestone. A good milestone is a passing script/test addition, a durable design
update with simulator evidence, or a completed documentation/rule update.
