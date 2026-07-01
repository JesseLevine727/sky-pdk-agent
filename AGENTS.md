# AGENTS.md

## Repository Mission

This repo is a file-based analog-design assistant for SKY130. Codex should edit
specifications, SPICE templates, scripts, layout Tcl, reports, and documentation,
then run deterministic tools and parse their outputs. Do not treat model output
as simulation, DRC, LVS, or PEX evidence.

## Required Working Loop

1. Start from a spec in `specs/`.
2. Render a testbench from a template under `circuits/*/testbenches/`.
3. Run ngspice, or state clearly when ngspice/PDK setup is missing.
4. Parse measurements into JSON under `circuits/*/reports/` or a run directory.
5. Compare measurements against the spec before proposing sizing changes.
6. Apply sizing changes only through specs, overrides, or scripted transforms.
7. Re-run simulation after changes whenever the tools are available.
8. Run `make eval-ota` before treating schematic behavior as stable across
   named corners and load cases.
9. Use `make eval-current-mirror` as the smoke pattern for adding a simpler
   one-testbench analog block.
10. Use `make plan-opamp-comparator-chain` as the reference pattern for turning
   a natural-language-style mixed-signal request into a file-based plan.
11. Use `make eval-comparator` before
   `make eval-opamp-comparator-chain` when validating the OTA-to-comparator
   mixed-signal chain.
12. Use `make agent-ota` for bounded recursive sizing loops when multiple
   evaluation cases miss or trade off against each other.
13. Use `make search-ota` for configured schematic candidate axes, and
    `make search-ota-postlayout-quick` when schematic winners may trade off
    against layout parasitics.
14. After schematic closure, run physical targets in order:
    `make layout-ota`, `make drc-ota`, `make lvs-ota`, `make pex-ota`, and
    `make postlayout-ota`.
15. Prefer `make signoff-ota` when the goal is complete end-to-end evidence
    rather than debugging one physical stage.

## Verification Rules

- Never claim a circuit meets spec unless the relevant script ran successfully
  and produced measurements from the EDA tool.
- Keep generated run artifacts under `circuits/**/sim/runs/`.
- Keep durable reports under `circuits/**/reports/`.
- If `PDK_ROOT`, `PDK`, ngspice, Xschem, Magic, KLayout, or Netgen are missing,
  report exactly which dependency blocked verification.
- Treat DRC, LVS, and PEX scripts as signoff gates, not advisory checks.
- Keep SPICE model paths configurable through `PDK_ROOT` and `PDK`; do not
  hardcode a personal absolute PDK path.
- Layout generators should emit machine-readable intent manifests when
  practical, but those manifests are not substitutes for DRC, LVS, PEX, or
  post-layout simulation evidence.
- `make eval-ota` is an exploratory evaluation target: it should complete if
  all simulations run, even when cases miss spec. Use `make eval-ota-strict`
  when a hard pass/fail gate is required.
- `make eval-current-mirror` is a strict one-testbench block-template check.
  Treat it as the reference pattern for simple new analog cells.
- `make eval-comparator` and `make eval-opamp-comparator-chain` are strict
  transient checks for the mixed-signal intake example. Treat the chain report
  as interface evidence, not standalone opamp or comparator closure.
- `make agent-ota` ranks candidate sizing changes but does not change the source
  spec. `make agent-ota-apply` may update the spec only when the best candidate
  passes every named evaluation case.
- `make drc-ota` must report zero Magic DRC errors before any LVS/PEX claim.
- `make lvs-ota` must report `Netlists match uniquely` before treating layout
  connectivity as closed.
- `make postlayout-ota` is a deterministic extracted-netlist evaluation gate.
  Treat any target miss as a real post-layout design miss, even when schematic
  evaluation passes.
- `make signoff-ota` must pass every configured stage before an end-to-end
  physical closure claim.
- `make search-ota-postlayout-quick` may show schematic candidates that fail
  post-layout. Treat those as useful evidence of layout/schematic tradeoff, not
  as passing design candidates.

## Git Rules

- Commit and push after each coherent verified milestone during long agentic
  work. Do not wait until the whole roadmap is complete.
- Keep commits scoped: source flow changes, design sizing changes, and generated
  durable reports may be separate milestones when that makes review clearer.
- Do not commit generated run directories under `circuits/**/sim/runs/`.
- Do commit durable Markdown reports under `circuits/**/reports/` when they
  summarize a verified milestone.

## Coding Rules

- Prefer Python standard library plus PyYAML for flow scripts.
- Keep script outputs machine-readable when they feed another agent step.
- Do not hand-edit generated simulation netlists in run directories; edit the
  source spec or template instead.
- Keep shell scripts POSIX-ish Bash with `set -euo pipefail`.
- Run `make check` after changing scripts or skill files.
