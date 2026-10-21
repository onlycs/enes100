.PHONY: flash dev

flash:
	mpremote cp -r src/. : + reset

dev:
	watchexec -r -w src -- mpremote mount src + run src/main.py
