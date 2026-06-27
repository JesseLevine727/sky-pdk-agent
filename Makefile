PYTHON ?= python3
REPO_ROOT := $(CURDIR)
export PATH := $(REPO_ROOT)/bin:$(REPO_ROOT)/.tools/apt/usr/bin:$(PATH)
export LD_LIBRARY_PATH := $(REPO_ROOT)/.tools/apt/usr/lib/klayout:$(REPO_ROOT)/.tools/apt/usr/lib/x86_64-linux-gnu:$(LD_LIBRARY_PATH)
export PDK_ROOT ?= $(HOME)/.ciel
export PDK ?= sky130A
SPEC ?= specs/ota.yaml
PRIMITIVE_SPEC ?= specs/primitive_nmos.yaml
OTA_TEMPLATE ?= circuits/ota/testbenches/ota_ac.spice.in
PRIMITIVE_TEMPLATE ?= circuits/primitives/nmos_id_vgs/testbenches/id_vgs.spice.in

.PHONY: check tools render-ota sim-ota eval-ota eval-ota-strict agent-ota agent-ota-apply agent-ota-smoke render-primitive sim-primitive propose-ota sweep-ota skill-validate

check: tools skill-validate
	$(PYTHON) -m unittest discover -s tests
	$(PYTHON) -m py_compile scripts/*.py

tools:
	$(PYTHON) scripts/check_tools.py --soft

render-ota:
	$(PYTHON) scripts/run_ngspice.py --spec $(SPEC) --template $(OTA_TEMPLATE) --out-dir circuits/ota/sim/runs/render --dry-run

sim-ota:
	$(PYTHON) scripts/run_ngspice.py --spec $(SPEC) --template $(OTA_TEMPLATE) --out-dir circuits/ota/sim/runs/latest

eval-ota:
	$(PYTHON) scripts/evaluate_ota.py --spec $(SPEC) --template $(OTA_TEMPLATE) --out-dir circuits/ota/sim/runs/eval --report circuits/ota/reports/latest_eval.md

eval-ota-strict:
	$(PYTHON) scripts/evaluate_ota.py --spec $(SPEC) --template $(OTA_TEMPLATE) --out-dir circuits/ota/sim/runs/eval --report circuits/ota/reports/latest_eval.md --strict

agent-ota: tools
	$(PYTHON) scripts/agent_loop.py --spec $(SPEC) --template $(OTA_TEMPLATE) --out-dir circuits/ota/sim/runs/agent_loop --report circuits/ota/reports/agent_loop.md --max-candidates 6

agent-ota-apply: tools
	$(PYTHON) scripts/agent_loop.py --spec $(SPEC) --template $(OTA_TEMPLATE) --out-dir circuits/ota/sim/runs/agent_loop --report circuits/ota/reports/agent_loop.md --max-candidates 8 --apply-best

agent-ota-smoke:
	$(PYTHON) scripts/agent_loop.py --spec $(SPEC) --template $(OTA_TEMPLATE) --out-dir circuits/ota/sim/runs/agent_loop_smoke --report circuits/ota/reports/agent_loop_smoke.md --max-candidates 3 --plan-only

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
