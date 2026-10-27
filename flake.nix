{
  description = "enes100";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs { inherit system; };

        applications = with pkgs; [
          mpremote
          picotool

          python3
          pyright
          ruff

          watchexec

          nil
          nixd

          gnumake
        ];
      in
      {
        devShells.default = pkgs.mkShell {
          packages = applications;

          shellHook = ''
            if [ ! -d .venv ]; then
              virtualenv .venv
              .venv/bin/pip install -q micropython-rp2-rpi_pico2-stubs
            fi
          '';
        };
      }
    );
}
