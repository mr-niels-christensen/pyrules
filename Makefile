PYFILES := $(shell find src -name "*.py")
VENV := venv

.PHONY: all
all: test

.PHONY: clean
clean:
	@rm .*.made
	@rm -rf $(VENV)

.PHONY: test
test: .pep8.made .unittest.made

.pep8.made: $(VENV)/bin/activate $(PYFILES)
	@source $(VENV)/bin/activate && \
	@echo $(PYFILES) | xargs pep8
	@touch $@
	
$(VENV)/bin/activate:
	virtualenv $(VENV) && \
	source $(VENV)/bin/activate && \
	pip install pep8

.unittest.made: $(VENV)/bin/activate $(PYFILES)
	@source $(VENV)/bin/activate && \
	python -m unittest discover -s src/test -t src
	@touch $@
