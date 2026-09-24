{
  description = "ENES100 Arduino (Uno) development environment";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      forAllSystems = f:
        nixpkgs.lib.genAttrs systems (system: f nixpkgs.legacyPackages.${system});
    in
    {
      devShells = forAllSystems (pkgs: {
        default = pkgs.mkShell {
          name = "enes100-arduino";

          packages = with pkgs; [
            arduino-cli # compile / upload / serial monitor
            clang-tools # clangd: editor completion, via compile_commands.json
            jq # merges the per-sketch compile databases
            gnumake
            git
          ];

          # arduino-cli downloads a prebuilt AVR toolchain (avr-gcc, avrdude).
          # Those are ordinary FHS binaries, so they need nix-ld to run.
          NIX_LD = pkgs.lib.fileContents "${pkgs.stdenv.cc}/nix-support/dynamic-linker";
          NIX_LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
            pkgs.stdenv.cc.cc.lib
            pkgs.zlib
            pkgs.ncurses
            pkgs.libusb1
            pkgs.systemd # libudev, for avrdude port enumeration
          ];

          shellHook = ''
            # Keep every Arduino core, library and download inside this repo
            # instead of ~/.arduino15 and ~/Arduino.
            root="$(git rev-parse --show-toplevel 2>/dev/null || echo "$PWD")"
            export ARDUINO_DIRECTORIES_DATA="$root/.arduino/data"
            export ARDUINO_DIRECTORIES_DOWNLOADS="$root/.arduino/downloads"
            export ARDUINO_DIRECTORIES_USER="$root/.arduino/user"
            export ARDUINO_CONFIG_FILE="$root/arduino-cli.yaml"
          '';
        };
      });
    };
}
