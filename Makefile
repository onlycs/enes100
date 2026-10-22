MPREMOTE ?= mpremote
PORT     ?= auto
MP        = $(MPREMOTE) connect $(PORT)

.PHONY: setup flash dev

flash:
	$(MP) cp -r src/. : + reset

setup:
	$(MP) mip install github:josverl/micropython-stubs/mip/typing.json

dev:
	watchexec -r -w src -- $(MP) mount src + run src/main.py
