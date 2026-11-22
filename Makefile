PYTHON ?= python3
export PYTHONPATH := src

.PHONY: test run demo demo-abs demo-vectors clean

test:
	$(PYTHON) -m unittest discover -s tests -t . -v

run:
	mkdir -p build
	$(PYTHON) -m uvm examples/spec_tests.asm build/spec_tests.bin --test

demo:
	mkdir -p build
	$(PYTHON) -m uvm examples/copy_array.asm build/copy_array.bin
	$(PYTHON) -m uvm.interpreter build/copy_array.bin build/copy_array.xml 10:24
	cat build/copy_array.xml

demo-abs:
	mkdir -p build
	$(PYTHON) -m uvm examples/abs_demo.asm build/abs_demo.bin
	$(PYTHON) -m uvm.interpreter build/abs_demo.bin build/abs_demo.xml 30:44
	cat build/abs_demo.xml

demo-vectors:
	mkdir -p build
	set -e; for name in vector_abs example_mixed example_negative example_boundaries; do \
		echo "== $$name"; \
		$(PYTHON) -m uvm examples/stage5/$$name.asm build/$$name.bin; \
		$(PYTHON) -m uvm.interpreter build/$$name.bin build/$$name.xml 0:9; \
		cat build/$$name.xml; echo; \
	done

clean:
	rm -rf build
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
