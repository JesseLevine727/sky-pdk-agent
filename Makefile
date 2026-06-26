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

.PHONY: check tools render-ota sim-ota render-primitive sim-primitive propose-ota sweep-ota skill-validate

check: tools skill-validate
	$(PYTHON) -m unittest discover -s tests
	$(PYTHON) -m py_compile scripts/*.py

tools:
	$(PYTHON) scripts/check_tools.py --soft

render-ota:
	$(PYTHON) scripts/run_ngspice.py --spec $(SPEC) --template $(OTA_TEMPLATE) --out-dir circuits/ota/sim/runs/render --dry-run

sim-ota:
	$(PYTHON) scripts/run_ngspice.py --spec $(SPEC) --template $(OTA_TEMPLATE) --out-dir circuits/ota/sim/runs/latest

render-primitive:
	$(PYTHON) scripts/run_ngspice.py --spec $(PRIMITIVE_SPEC) --template $(PRIMITIVE_TEMPLATE) --out-dir circuits/primitives/nmos_id_vgs/sim/runs/render --dry-run

sim-primitive:
	$(PYTHON) scripts/run_ngspice.py --spec $(PRIMITIVE_SPEC) --template $(PRIMITIVE_TEMPLATE) --out-dir circuits/primitives/nmos_id_vgs/sim/runs/latest

propose-ota:
	$(PYTHON) scripts/propose_sizing.py --spec $(SPEC) --measures circuits/ota/sim/runs/latest/measures.json --out circuits/ota/reports/sizing_proposal.json

sweep-ota:
	$(PYTHON) scripts/sweep_ota.py --spec $(SPEC) --template $(OTA_TEMPLATE) --out-dir circuits/ota/sim/runs/sweep

skill-validate:
	$(PYTHON) scripts/validate_skill.py .agents/skills/analog-design
