# Variables
PYTHON = python3
PIP = $(PYTHON) -m pip
VENV = backend/venv
NPM = npm

# Colors
GREEN = \033[0;32m
BLUE = \033[0;34m
YELLOW = \033[0;33m
RED = \033[0;31m
MAGENTA = \033[0;35m
CYAN = \033[0;36m
BOLD = \033[1m
RESET = \033[0m

SCHEMA_DIR_WS = $(CURDIR)/backend/protocol/websocket
GEN_DIR_PY_WS   = $(CURDIR)/backend/protocol/generated/websocket
GEN_FILE_TS_WS   = $(CURDIR)/frontend/src/codegen/websocket


all: help

python-setup:
	@echo "$(BLUE)Setting up Python virtual environment...$(RESET)"
	@$(PYTHON) -m venv $(VENV) 2> /dev/null
	@echo "$(GREEN)Virtual environment created at $(VENV)$(RESET)"
	@echo "$(BLUE)Installing Python dependencies...$(RESET)"
	@$(VENV)/bin/$(PIP) install -r backend/requirements/base.txt > /dev/null
	@echo "$(GREEN)Python dependencies installed.$(RESET)"

codegen:
	@datamodel-codegen \
		--input $(SCHEMA_DIR_WS) \
		--input-file-type jsonschema \
		--output $(GEN_DIR_PY_WS) \
		--enum-field-as-literal=all \
		--output-model-type pydantic_v2.BaseModel \
		--strict-nullable \
		--collapse-root-models \
		> /dev/null
	cd $(SCHEMA_DIR_WS) && npx json2ts --input '*.json' --output $(GEN_FILE_TS_WS) > /dev/null
	@echo "$(GREEN)python + typescript models (re)generated.$(RESET)"


js-install:
	@echo "$(BLUE)Installing npm dependencies...$(RESET)"
	@cd frontend && $(NPM) install > /dev/null
	@echo "$(GREEN)npm dependencies installed.$(RESET)"

setup: python-setup js-install codegen
	@echo "$(GREEN)$(BOLD)Project setup complete.$(RESET)"
	@echo ""
	@echo "$(YELLOW)Activate the virtual environment with: $(BOLD)source $(VENV)/bin/activate$(RESET)"

help:
	@echo "$(RED)           _ _                       _                                $(RESET)"
	@echo "$(RED) _ __ ___ (_) |_ _ __  _   _ _______| | ___  ___   ___ ___  _ __ ___  $(RESET)"
	@echo "$(RED)| '_ \` _ \| | __| '_ \| | | |_  /_  / |/ _ \/ __| / __/ _ \| '_ \` _ \ $(RESET)"
	@echo "$(RED)| | | | | | | |_| |_) | |_| |/ / / /| |  __/\__ \| (_| (_) | | | | | |$(RESET)"
	@echo "$(RED)|_| |_| |_|_|\__| .__/ \__,_/___/___|_|\___||___(_)___\___/|_| |_| |_|$(RESET)"
	@echo "$(RED)                |_|                                                   $(RESET)"
	@echo "$(BOLD)Available targets:$(RESET)"
	@echo "  $(GREEN)setup$(RESET)        	- Set up the entire project (Python and JavaScript)"
	@echo "  $(BLUE)codegen$(RESET)      	- Generate code (currently only for websocket protocol)"
	@echo "  $(RED)clean$(RESET)        	- Remove generated directories and files"
	@echo "  $(YELLOW)test$(RESET)        	- Run all tests (Python and JavaScript)"
	@echo "  $(YELLOW)lint$(RESET)         	- Run all linters (Python and JavaScript)"
	@echo ""
	@echo "$(MAGENTA)Python targets:$(RESET)"
	@echo "  $(GREEN)python-setup$(RESET)   - Create Python virtual environment"
	@echo "  $(YELLOW)python-test$(RESET)    - Run Python tests"
	@echo "  $(YELLOW)python-lint$(RESET)    - Lint Python code"
	@echo ""
	@echo "$(MAGENTA)JavaScript targets:$(RESET)"
	@echo "  $(GREEN)js-install$(RESET)     - Install npm dependencies"
	@echo "  $(BLUE)js-build$(RESET)       - Build the frontend"
	@echo "  $(BLUE)js-dev$(RESET)         - Start the frontend development server"
	@echo "  $(YELLOW)js-test$(RESET)        - Run JavaScript tests"
	@echo "  $(YELLOW)js-lint$(RESET)        - Lint JavaScript code"
