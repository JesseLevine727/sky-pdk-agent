PYTHON ?= python3
REPO_ROOT := $(CURDIR)
export PATH := $(REPO_ROOT)/bin:$(REPO_ROOT)/.tools/apt/usr/bin:$(PATH)
export LD_LIBRARY_PATH := $(REPO_ROOT)/.tools/apt/usr/lib/klayout:$(REPO_ROOT)/.tools/apt/usr/lib/x86_64-linux-gnu:$(LD_LIBRARY_PATH)
export PDK_ROOT ?= $(HOME)/.ciel
export PDK ?= sky130A
SPEC ?= specs/ota.yaml
PRIMITIVE_SPEC ?= specs/primitive_nmos.yaml
OTA_TEMPLATE ?= circuits/ota/testbenches/ota_ac.spice.in
OTA_POSTLAYOUT_TEMPLATE ?= circuits/ota/testbenches/ota_ac_postlayout.spice.in
PRIMITIVE_TEMPLATE ?= circuits/primitives/nmos_id_vgs/testbenches/id_vgs.spice.in
OTA_LAYOUT_DIR ?= circuits/ota/layout/magic
OTA_LAYOUT ?= $(OTA_LAYOUT_DIR)/ota_5t.mag
OTA_EXTRACTED ?= circuits/ota/layout/extracted/ota_5t_extracted.spice
OTA_LVS_EXTRACTED ?= circuits/ota/layout/extracted/ota_5t_lvs.spice

.PHONY: check tools netlist-ota render-ota sim-ota eval-ota eval-ota-strict agent-ota agent-ota-apply agent-ota-smoke render-primitive sim-primitive propose-ota sweep-ota layout-ota drc-ota extract-ota-lvs pex-ota lvs-ota postlayout-ota signoff-ota skill-validate

check: tools skill-validate
	$(PYTHON) -m unittest discover -s tests
	$(PYTHON) -m py_compile scripts/*.py

tools:
	$(PYTHON) scripts/check_tools.py --soft

netlist-ota:
	$(PYTHON) scripts/render_ota_cell.py --spec $(SPEC) --out circuits/ota/schematic/ota_5t.spice

render-ota: netlist-ota
	$(PYTHON) scripts/run_ngspice.py --spec $(SPEC) --template $(OTA_TEMPLATE) --out-dir circuits/ota/sim/runs/render --dry-run

sim-ota: netlist-ota
	$(PYTHON) scripts/run_ngspice.py --spec $(SPEC) --template $(OTA_TEMPLATE) --out-dir circuits/ota/sim/runs/latest

eval-ota: netlist-ota
	$(PYTHON) scripts/evaluate_ota.py --spec $(SPEC) --template $(OTA_TEMPLATE) --out-dir circuits/ota/sim/runs/eval --report circuits/ota/reports/latest_eval.md

eval-ota-strict: netlist-ota
	$(PYTHON) scripts/evaluate_ota.py --spec $(SPEC) --template $(OTA_TEMPLATE) --out-dir circuits/ota/sim/runs/eval --report circuits/ota/reports/latest_eval.md --strict

agent-ota: tools netlist-ota
	$(PYTHON) scripts/agent_loop.py --spec $(SPEC) --template $(OTA_TEMPLATE) --out-dir circuits/ota/sim/runs/agent_loop --report circuits/ota/reports/agent_loop.md --max-candidates 6

agent-ota-apply: tools netlist-ota
	$(PYTHON) scripts/agent_loop.py --spec $(SPEC) --template $(OTA_TEMPLATE) --out-dir circuits/ota/sim/runs/agent_loop --report circuits/ota/reports/agent_loop.md --max-candidates 8 --apply-best

agent-ota-smoke: netlist-ota
	$(PYTHON) scripts/agent_loop.py --spec $(SPEC) --template $(OTA_TEMPLATE) --out-dir circuits/ota/sim/runs/agent_loop_smoke --report circuits/ota/sim/runs/agent_loop_smoke/report.md --max-candidates 3 --plan-only

layout-ota: netlist-ota
	$(PYTHON) scripts/generate_ota_magic_layout.py --spec $(SPEC) --out-dir $(OTA_LAYOUT_DIR) --run

drc-ota: layout-ota
	scripts/run_magic_drc.sh $(OTA_LAYOUT) circuits/ota/reports/drc

pex-ota: layout-ota
	scripts/run_magic_pex.sh $(OTA_LAYOUT) ota_5t $(OTA_EXTRACTED)

extract-ota-lvs: layout-ota
	scripts/run_magic_extract_lvs.sh $(OTA_LAYOUT) ota_5t $(OTA_LVS_EXTRACTED)

lvs-ota: netlist-ota extract-ota-lvs
	scripts/run_netgen_lvs.sh $(OTA_LVS_EXTRACTED) circuits/ota/schematic/ota_5t.spice ota_5t circuits/ota/reports/lvs_ota.md

postlayout-ota: pex-ota
	$(PYTHON) scripts/evaluate_ota.py --spec $(SPEC) --template $(OTA_POSTLAYOUT_TEMPLATE) --out-dir circuits/ota/sim/runs/postlayout_eval --report circuits/ota/reports/postlayout_eval.md

signoff-ota:
	$(PYTHON) scripts/signoff_block.py --spec $(SPEC) --report circuits/ota/reports/signoff_summary.md --json circuits/ota/reports/signoff_summary.json

render-primitive:
	$(PYTHON) scripts/run_ngspice.py --spec $(PRIMITIVE_SPEC) --template $(PRIMITIVE_TEMPLATE) --out-dir circuits/primitives/nmos_id_vgs/sim/runs/render --dry-run

sim-primitive:
	$(PYTHON) scripts/run_ngspice.py --spec $(PRIMITIVE_SPEC) --template $(PRIMITIVE_TEMPLATE) --out-dir circuits/primitives/nmos_id_vgs/sim/runs/latest

propose-ota:
	$(PYTHON) scripts/propose_sizing.py --spec $(SPEC) --measures circuits/ota/sim/runs/latest/measures.json --out circuits/ota/reports/sizing_proposal.json

sweep-ota:
	$(PYTHON) scripts/sweep_ota.py --spec $(SPEC) --template $(OTA_TEMPLATE) --out-dir circuits/ota/sim/runs/sweep

sweep-ota-quick:
	$(PYTHON) scripts/sweep_ota.py --spec $(SPEC) --template $(OTA_TEMPLATE) --out-dir circuits/ota/sim/runs/sweep_quick --max-candidates 12

skill-validate:
	$(PYTHON) scripts/validate_skill.py .agents/skills/analog-design
