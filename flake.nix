{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { nixpkgs, flake-utils, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
        qt = pkgs.libsForQt5.qt5;
        py = pkgs.python311Packages;
      in {
        devShells.default = pkgs.mkShell {
          nativeBuildInputs = [ py.pyqt5 py.datetime py.pandas py.plyer py.requests qt.qtbase ];
          QT_QPA_PLATFORM_PLUGIN_PATH="${qt.qtbase.bin}/lib/qt-${qt.qtbase.version}/plugins";
        };
      });
}
