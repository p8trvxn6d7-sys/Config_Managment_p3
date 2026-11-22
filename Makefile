PYTHON ?= python3
export PYTHONPATH := src

.PHONY: test run clean

test:
	$(PYTHON) -m unittest discover -s tests -t . -v

run:
	mkdir -p build
	$(PYTHON) -m uvm examples/spec_tests.asm build/spec_tests.bin --test

clean:
	rm -rf build
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
