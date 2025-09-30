{
  description = "Dev shell and CI for xeno-mathematics-engine";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.05";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; overlays = []; };
        python = pkgs.python311;
        pythonEnv = python.withPackages (ps: with ps; [
          pip
          setuptools
          wheel
        ]);
      in {
        devShells.default = pkgs.mkShell {
          name = "xeno-dev";
          packages = [
            pythonEnv
            pkgs.pre-commit
            pkgs.git
            pkgs.ruff
            pkgs.python311Packages.mypy
            pkgs.poetry
            pkgs.nodejs_20
            pkgs.docker-client
            pkgs.syft
            pkgs.cosign
          ];
          shellHook = ''
            export PIP_DISABLE_PIP_VERSION_CHECK=1
            export PIP_NO_INPUT=1
            echo "xeno shell ready (python $(python --version))"
          '';
        };
      });
}


