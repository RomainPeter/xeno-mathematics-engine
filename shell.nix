let
  flake = import (builtins.getFlake ".");
in flake.devShells.${builtins.currentSystem}.default


