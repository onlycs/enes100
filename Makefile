MPREMOTE ?= mpremote
PORT     ?= auto
MP        = $(MPREMOTE) connect $(PORT)

PYTHON    ?= python3
STUBS_PKG ?= micropython-rp2-rpi_pico2-stubs
TYPESHED   = typeshed
PID_SRC    = github:gastmaier/micropython-simple-pid/simple_pid/PID.py@master
PID_URL    = https://raw.githubusercontent.com/gastmaier/micropython-simple-pid/master/simple_pid/PID.py

.PHONY: setup flash dev

flash:
	$(MP) cp -r src/. : + reset

setup: typeshed
	$(MP) mip install github:josverl/micropython-stubs/mip/typing.json
	$(MP) mip install logging
	$(MP) mip install github:gastmaier/micropython-simple-pid/simple_pid/PID.py@master

typeshed: Makefile stubs/PID.pyi stubs/ndarray.pyi
	rm -rf typeshed
	python3 -m pip install -q --no-user --target typeshed micropython-typeshed

	install -D stubs/PID.pyi typeshed/stubs/simple-pid/PID.pyi

	@set -eu; \
	tmp=$$(mktemp -d); \
	trap 'rm -rf "$$tmp"' EXIT; \
	python3 -m pip install -q --no-user --no-deps --target "$$tmp" circuitpython-stubs; \
	test -f "$$tmp/ulab-stubs/numpy/__init__.pyi" || { echo "ulab.numpy stubs not found" >&2; exit 1; }; \
	cp -R "$$tmp/ulab-stubs" typeshed/stdlib/ulab; \
	echo "ulab: 3.0-" >> typeshed/stdlib/VERSIONS; \
	sed -i.bak 's/^import ulab$$/import ulab.numpy/' typeshed/stdlib/ulab/numpy/__init__.pyi; \
	sed -i.bak '/^class ndarray: \.\.\.$$/d' typeshed/stdlib/ulab/numpy/__init__.pyi; \
	rm -f typeshed/stdlib/ulab/numpy/__init__.pyi.bak; \
	cat stubs/ndarray.pyi >> typeshed/stdlib/ulab/numpy/__init__.pyi

	@echo "MicroPython typeshed ready."

dev:
	watchexec -r -w src -- $(MP) mount src + run src/main.py
