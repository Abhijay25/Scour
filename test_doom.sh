#!/bin/sh
# Run this directly from your terminal to debug terminal-doom
BIN="$HOME/.local/share/scour/doom/terminal-doom-bin"
WAD="$HOME/.local/share/scour/doom/doom1.wad"

echo "Binary: $BIN (exists: $(test -f "$BIN" && echo yes || echo no))"
echo "WAD: $WAD (exists: $(test -f "$WAD" && echo yes || echo no))"
echo "TERM_PROGRAM: $TERM_PROGRAM"
echo "TMUX: ${TMUX:-not set}"
echo ""
echo "Launching terminal-doom..."
cd "$HOME/.local/share/scour/doom"
"$BIN" -iwad "$WAD"
echo "Exit code: $?"
