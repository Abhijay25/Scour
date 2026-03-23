{
  description = "Scour – competitive research TUI";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        python = pkgs.python312;
        pythonPkgs = python.pkgs;
      in
      {
        devShells.default = pkgs.mkShell {
          packages = [
            python
            pythonPkgs.pip
            pythonPkgs.textual
            pythonPkgs.httpx
            pythonPkgs.python-dotenv
          ];

          shellHook = ''
            # Install the package in editable mode into a local venv
            # so the `scour` command is available
            if [ ! -d .venv ]; then
              python -m venv .venv
            fi
            source .venv/bin/activate
            pip install -e . --quiet 2>/dev/null
          '';
        };
      }
    );
}
