# Agentic Analog Loop

This repo now has a deterministic Codex-in-the-loop analog workflow for the 5T
OTA. The loop is file-based: Codex edits specs and scripts, EDA tools generate
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
```

`make agent-ota` never edits the source spec. It writes:

- `circuits/ota/reports/agent_loop.md`
- `circuits/ota/sim/runs/agent_loop/agent_loop.json`
- per-candidate eval run directories under `circuits/ota/sim/runs/agent_loop/`

`make agent-ota-apply` only writes back to `specs/ota.yaml` when the best
candidate passes every named evaluation case.

## Current OTA Finding

The current nominal OTA passes. The multi-case eval still has coupled tradeoffs:
slow-corner gain and heavy-load bandwidth push sizing in opposite directions.

The recursive loop improved the design search from 2/4 passing cases to 3/4.
Best candidate:

```text
bias_tail_v=0.7
devices.mn_in.l_um=1.05
devices.mn_in.w_um=15.12
devices.mp_load.l_um=1.05
```

That candidate still misses slow-corner gain slightly, so it was not applied.

## Next Stack Stages

1. Broaden sizing intelligence with a gm/ID or primitive characterization table.
2. Add an Xschem schematic source and verify netlist equivalence to the current
   SPICE template.
3. Add a Magic layout template for the 5T OTA.
4. Run DRC, LVS, PEX, and post-layout `make eval-ota`.
5. Promote post-layout eval and signoff reports to the same recursive loop.
