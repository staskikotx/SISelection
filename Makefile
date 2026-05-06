.PHONY: run test test_extract test_remote_qwen
PYTHON=python3
SCRIPTS_DIR=src

PYTHONPATH := $(SCRIPTS_DIR):$(shell pwd):$(PYTHONPATH)
export PYTHONPATH 

run: 
	$(PYTHON) $(SCRIPTS_DIR)/run_on_bird.py

test: 
	$(PYTHON) test_select.py
test_extract: 
	$(PYTHON) test_with_extract_candidates.py
test_remote_qwen:
	$(PYTHON) test_remote_qwen.py
