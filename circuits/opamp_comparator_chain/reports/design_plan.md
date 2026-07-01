# Design Intake Plan

- Design: `opamp_comparator_chain`
- Intent source: `intents/opamp_comparator_chain.yaml`
- Topology: `ota_frontend_static_cmos_comparator`

## Intent

Design a 1.8 V mixed-signal analog front end where an OTA amplifies a small
sensor threshold crossing and drives a static CMOS comparator. The chain
should switch correctly across the nominal SKY130 simulation setup, stay
below 1 mW, and provide deterministic files and reports that Codex can use
for recursive block-level and chain-level improvement.

## Blocks

| Block | Kind | Role |
| --- | --- | --- |
| `opamp` | `ota_5t` | Amplify the sensor-reference differential input. |
| `comparator` | `static_cmos_comparator` | Convert the amplified analog node into a rail-level decision. |
| `opamp_comparator_chain` | `hierarchical_mixed_signal_testbench` | Verify opamp/comparator interface behavior and full-chain timing. |

## Interfaces

- `opamp.out` -> `comparator.vin`: The OTA output must cross the comparator threshold with enough margin.
- `sensor_input` -> `opamp.inp`: The sensor step is compared against the reference input.
- `comparator.out` -> `digital_decision`: The static CMOS output is the digital-like chain decision.

## Planned Files

- `circuits/opamp_comparator_chain/reports/design_plan.md`
- `circuits/comparator/reports/latest_eval.md`
- `circuits/opamp_comparator_chain/reports/latest_eval.md`
- `circuits/opamp_comparator_chain/reports/design_notes.md`
- `circuits/comparator/schematic/static_comparator.spice`
- `specs/comparator.yaml`
- `specs/opamp_comparator_chain.yaml`
- `circuits/comparator/testbenches/comparator_tran.spice.in`
- `circuits/opamp_comparator_chain/testbenches/chain_tran.spice.in`

## Acceptance Commands

- `make plan-opamp-comparator-chain`
- `make eval-comparator`
- `make eval-opamp-comparator-chain`
- `make check`

## Acceptance Checks

- Comparator transient evaluation passes all configured targets.
- Chain transient evaluation passes all configured targets.
- All generated simulation evidence remains under circuits/**/sim/runs/.
- Durable Markdown reports summarize the verified milestone.

## Agent Loop

- Parse the user request into this intent file.
- Generate or update block specs, schematics, testbenches, and reports.
- Run comparator evaluation before full-chain evaluation.
- If the chain misses, classify the miss as opamp, comparator, or interface.
- Modify only specs, source schematics, testbenches, or scripts.
- Re-run the failing block and the integrated chain after every change.
