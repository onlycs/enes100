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

typeshed: Makefile stubs/PID.pyi
	rm -rf typeshed
	python3 -m pip install micropython-typeshed --target typeshed --no-user
	install -D stubs/PID.pyi typeshed/stubs/simple-pid/PID.pyi
	git clone -q --depth 1 --filter=blob:none --sparse \
		https://github.com/Josverl/micropython-stubs.git /tmp/micropython-stubs
	git -C /tmp/micropython-stubs sparse-checkout set stubs/micropython-ulab
	mkdir -p typeshed/stubs/ulab
	cp -r /tmp/micropython-stubs/stubs/micropython-ulab/ulab typeshed/stubs/ulab/
	rm -rf /tmp/micropython-stubs


dev:
	watchexec -r -w src -- $(MP) mount src + run src/main.py
