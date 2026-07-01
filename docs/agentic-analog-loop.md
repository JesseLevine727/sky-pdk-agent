# Agentic Analog Loop

This repo has a deterministic Codex-in-the-loop analog workflow for the 5T OTA.
The loop is file-based: Codex edits specs and scripts, EDA tools generate
evidence, and reports summarize decisions.

## Implemented Loop

```text
check tools -> evaluate baseline -> mine misses -> generate candidates
            -> evaluate candidates -> rank -> optionally apply passing best
            -> rerun checks -> commit/push milestone
```

Commands:

```bash
make check
make eval-ota
make agent-ota
make agent-ota-apply
make search-ota
make search-ota-postlayout-quick
make signoff-ota
```

`make agent-ota` never edits the source spec. It writes:

- `circuits/ota/reports/agent_loop.md`
- `circuits/ota/sim/runs/agent_loop/agent_loop.json`
- per-candidate eval run directories under `circuits/ota/sim/runs/agent_loop/`

`make agent-ota-apply` only writes back to `specs/ota.yaml` when the best
candidate passes every named evaluation case.

## Current OTA State

The current OTA passes schematic and extracted-layout evaluation. The physical
closure point is:

- `devices.mn_in.w_um=15.12`
- `devices.mp_load.w_um=26`
- `bias_tail_v=0.7`

`make search-ota` shows that `devices.mp_load.w_um=24` ranks slightly better
schematically. `make search-ota-postlayout-quick` then takes the top schematic
candidates through isolated layout/PEX/post-layout signoff and re-ranks
`devices.mp_load.w_um=26` first because it passes post-layout while the `24um`
PMOS load candidate fails extracted slow-corner gain.

## Next Stack Stages

1. Broaden sizing intelligence with a gm/ID or primitive characterization table.
2. Add additional block templates that use the same spec/eval/report contract.
3. Generalize layout generation beyond OTA-specific placement/routing.
4. Add topology-level candidates, not only sizing-axis candidates.
5. Feed post-layout search outcomes back into proposal generation.
