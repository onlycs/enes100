WARNINGS ?= default
BAUD     ?= 115200

# Board autodetection: `arduino-cli board list` names both the port and the FQBN
# of whatever is plugged in, so neither is hardcoded. Override either one on the
# command line (make starter PORT=/dev/ttyACM1 FQBN=arduino:avr:uno) when
# detection guesses wrong or the board can't identify itself. FQBN_FALLBACK is
# what targets like `setup` use with nothing connected.
FQBN_FALLBACK  ?= arduino:renesas_uno:unor4wifi
BOARD_TIMEOUT  ?= 2s
BOARD_JQ := [.detected_ports[]? | select(.matching_boards[0].fqbn)][0] // empty | .port.address + " " + .matching_boards[0].fqbn

# Detected lazily and at most once per run, so targets that never look at PORT
# or FQBN (clean, cdb-merge) pay nothing for the discovery wait.
BOARD = $(if $(filter undefined,$(origin BOARD_CACHE)),$(eval BOARD_CACHE := $(shell arduino-cli board list --discovery-timeout $(BOARD_TIMEOUT) --json 2>/dev/null | jq -r '$(BOARD_JQ)')))$(BOARD_CACHE)

PORT ?= $(firstword $(BOARD))
FQBN ?= $(or $(word 2,$(BOARD)),$(FQBN_FALLBACK))

CORE = $(firstword $(subst :, ,$(FQBN))):$(word 2,$(subst :, ,$(FQBN)))

# One sketch per folder, always sketches/<name>/main.ino.
SKETCH_DIRS := $(patsubst %/,%,$(sort $(dir $(wildcard sketches/*/main.ino))))
SKETCHES    := $(notdir $(SKETCH_DIRS))

# arduino-cli insists the main file be named after its folder, so nothing is
# ever compiled from sketches/<name> directly: stage-<name> mirrors the folder
# into build/.stage/<name> with main.ino linked as <name>.ino, and that is what
# arduino-cli sees. CDB_JQ then maps both the generated .ino.cpp and the staged
# symlinks back to the real sources, so clangd opens the files you edit.
STAGE := build/.stage

CDB_JQ := add | map(if (.file | test("/sketch/[^/]+\\.ino\\.cpp$$")) then ((.file | capture("/build/(?<n>[^/]+)/sketch/[^/]+\\.ino\\.cpp$$")) as $$m | ($$root + "/sketches/" + $$m.n + "/main.ino") as $$src | .file = $$src | .arguments = ([.arguments[0], "-x", "c++", "-include", "Arduino.h"] + (.arguments[1:] | map(if test("\\.ino\\.cpp$$") then $$src else . end)))) else . end) | map(.file |= gsub("/build/\\.stage/(?<n>[^/]+)/"; "/sketches/" + .n + "/") | .arguments |= map(gsub("/build/\\.stage/(?<n>[^/]+)/"; "/sketches/" + .n + "/")))

.PHONY: setup boards libs serial db cdb-merge clean distclean require-port nullopt

stage-%:
	@rm -rf $(STAGE)/$*
	@mkdir -p $(STAGE)/$*
	@for f in $(CURDIR)/sketches/$*/*; do \
		case $$f in \
			*/main.ino) ln -s $$f $(STAGE)/$*/$*.ino ;; \
			*) ln -s $$f $(STAGE)/$* ;; \
		esac; \
	done

define sketch_target
.PHONY: $(1) $(CURDIR)/sketches/$(1)
$(1) $(CURDIR)/sketches/$(1): require-port stage-$(1)
	arduino-cli compile --fqbn $$(FQBN) --build-path build/$(1) --warnings $$(WARNINGS) $$(STAGE)/$(1)
	arduino-cli upload --fqbn $$(FQBN) --port $$(PORT) --input-dir build/$(1) $$(STAGE)/$(1)
	@$$(MAKE) --no-print-directory cdb-merge
endef

noop:
	@echo "specify bro"

$(foreach s,$(SKETCHES),$(eval $(call sketch_target,$(s))))

setup: db
	arduino-cli config init --overwrite
	arduino-cli core update-index
	arduino-cli core install $(CORE)

boards:
	arduino-cli board list

libs:
	arduino-cli lib list

serial: require-port
	arduino-cli monitor --fqbn $(FQBN) --port $(PORT) --config baudrate=$(BAUD)

db: $(addprefix stage-,$(SKETCHES))
	@for s in $(SKETCHES); do \
		echo "compile database: $$s"; \
		arduino-cli compile --fqbn $(FQBN) --build-path build/$$s --only-compilation-database $(STAGE)/$$s >/dev/null; \
	done
	@$(MAKE) --no-print-directory cdb-merge

cdb-merge:
	@ls build/*/compile_commands.json >/dev/null 2>&1 || { echo "nothing built yet; run make db"; exit 1; }
	@jq -s --arg root "$(CURDIR)" '$(CDB_JQ)' build/*/compile_commands.json > compile_commands.json

clean:
	rm -rf build compile_commands.json

distclean: clean
	rm -rf .arduino arduino-cli.yaml

require-port:
	@test -n "$(PORT)" || { echo "No board detected. Plug it in (make boards to check), or pass PORT=/dev/ttyACM0"; exit 1; }
