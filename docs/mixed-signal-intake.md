# Mixed-Signal Design Intake

This repo now has a concrete path for turning a natural-language circuit
request into deterministic design work.

## Workflow

1. Codex translates the user request into an intent file under `intents/`.
2. `scripts/design_intake.py` validates the intent and writes a durable plan.
3. Codex creates or updates specs, schematics, testbenches, scripts, and
   reports listed by the plan.
4. Block-level evaluations run before integrated chain evaluations.
5. If the chain misses, Codex classifies the miss as a block or interface issue,
   edits source files, and reruns the failing block plus the chain.

The first implemented example is:

```bash
make plan-opamp-comparator-chain
make eval-comparator
make eval-opamp-comparator-chain
```

Evidence:

- Intent: `intents/opamp_comparator_chain.yaml`
- Plan: `circuits/opamp_comparator_chain/reports/design_plan.md`
- Comparator report: `circuits/comparator/reports/latest_eval.md`
- Chain report: `circuits/opamp_comparator_chain/reports/latest_eval.md`

## Current Example

The example request is an OTA front end feeding a static CMOS comparator. It is
implemented as a hierarchical transient simulation:

```text
sensor input -> 5T OTA -> static CMOS comparator -> digital-like decision
```

The committed nominal result passes:

- Comparator delay: `8.204048e-11 s`
- Comparator output high/low: `1.8 V` / `8.22067e-06 V`
- Chain OTA output: `0.3466185 V` initial, `1.414528 V` final
- Chain decision delay: `1.911959e-08 s`
- Chain output high/low: `1.799997 V` / `0.0001339365 V`
- Chain power: `3.11317e-05 W`

## Limits

The intake file is not an automatic topology inventor. It is a deterministic
contract that lets Codex turn a user description into explicit files, commands,
and acceptance checks. New arbitrary circuits still need a topology family,
testbench definitions, measurable targets, and signoff stages before they can
be treated as verified.
