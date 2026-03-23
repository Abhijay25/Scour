"""DOOM easter egg — runs terminal-doom (Kitty graphics protocol) in Ghostty/Kitty.

Falls back to a DOOM fire effect on unsupported terminals.
Ctrl+C to exit the game, 'q' or Esc to exit the fire effect.
"""

import os
import subprocess
import sys
from pathlib import Path

DOOM_DIR = Path.home() / ".local" / "share" / "scour" / "doom"
DOOM_BIN = DOOM_DIR / "terminal-doom-bin"
DOOM_WAD = DOOM_DIR / "doom1.wad"

ZIG_VERSION = "0.15.2"
ZIG_DIR = DOOM_DIR / f"zig-x86_64-linux-{ZIG_VERSION}"
REPO_DIR = DOOM_DIR / "terminal-doom"
REPO_URL = "https://github.com/cryptocode/terminal-doom.git"
REPO_TAG = f"zig-v{ZIG_VERSION}"
ZIG_TARBALL = f"https://ziglang.org/download/{ZIG_VERSION}/zig-x86_64-linux-{ZIG_VERSION}.tar.xz"


def _supports_kitty_graphics() -> bool:
    """Check if the terminal supports the Kitty graphics protocol."""
    term = os.environ.get("TERM_PROGRAM", "").lower()
    return term in ("ghostty", "kitty", "wezterm")


def _is_built() -> bool:
    return DOOM_BIN.exists() and DOOM_WAD.exists()


def _build_terminal_doom(on_status=None) -> bool:
    """Download Zig, clone terminal-doom, build it. Returns True on success."""
    import platform
    if platform.machine() not in ("x86_64", "AMD64"):
        return False

    DOOM_DIR.mkdir(parents=True, exist_ok=True)

    # Download Zig if needed
    if not ZIG_DIR.exists():
        if on_status:
            on_status("Downloading Zig compiler...")
        try:
            subprocess.run(
                ["sh", "-c", f'curl -sL "{ZIG_TARBALL}" | tar xJ'],
                cwd=str(DOOM_DIR), check=True, timeout=120,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False

    zig_bin = ZIG_DIR / "zig"
    if not zig_bin.exists():
        return False

    # Clone repo if needed
    if not REPO_DIR.exists():
        if on_status:
            on_status("Cloning terminal-doom...")
        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", "--branch", REPO_TAG, REPO_URL],
                cwd=str(DOOM_DIR), check=True, timeout=60,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False

    # Build
    if on_status:
        on_status("Building terminal-doom (this is a one-time step)...")
    try:
        subprocess.run(
            [str(zig_bin), "build", "-Doptimize=ReleaseFast"],
            cwd=str(REPO_DIR), check=True, timeout=300,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False

    built_bin = REPO_DIR / "zig-out" / "bin" / "terminal-doom"
    if not built_bin.exists():
        return False

    # Copy binary and WAD to clean locations
    DOOM_BIN.write_bytes(built_bin.read_bytes())
    DOOM_BIN.chmod(0o755)

    wad_src = REPO_DIR / "doom1.wad"
    if wad_src.exists() and not DOOM_WAD.exists():
        DOOM_WAD.write_bytes(wad_src.read_bytes())

    return _is_built()


def _run_terminal_doom() -> bool:
    """Run terminal-doom. Returns True if it ran successfully."""
    if not _is_built():
        return False
    result = subprocess.run(
        [str(DOOM_BIN), "-iwad", str(DOOM_WAD)],
        cwd=str(DOOM_DIR),
    )
    return result.returncode == 0


def _run_fire_effect() -> None:
    """Fallback: DOOM PSX fire effect in curses."""
    import curses
    import random
    import time

    CHARS = " .:-=+*#%@"
    LOGO = [
        r"  ___   ___   ___  __  __ ",
        r" |   \ / _ \ / _ \|  \/  |",
        r" | |) | (_) | (_) | |\/| |",
        r" |___/ \___/ \___/|_|  |_|",
    ]
    QUIT_HINT = "press q or Esc to exit"

    def loop(stdscr):
        curses.curs_set(0)
        stdscr.nodelay(True)
        stdscr.timeout(30)
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_BLACK)

        height, width = stdscr.getmaxyx()
        num = len(CHARS)
        mx = num - 1
        logo_rows = len(LOGO) + 2
        fh = height - logo_rows
        fw = width - 1
        if fh < 4 or fw < 10:
            return

        fire = [[0] * fw for _ in range(fh)]
        for x in range(fw):
            fire[fh - 1][x] = mx

        for i, line in enumerate(LOGO):
            lx = max(0, (width - len(line)) // 2)
            try:
                stdscr.addstr(i, lx, line, curses.A_BOLD | curses.color_pair(4))
            except curses.error:
                pass
        hx = max(0, (width - len(QUIT_HINT)) // 2)
        try:
            stdscr.addstr(len(LOGO), hx, QUIT_HINT, curses.A_DIM)
        except curses.error:
            pass

        def pair(v):
            f = v / mx
            return 1 if f < 0.25 else 2 if f < 0.55 else 3 if f < 0.8 else 4

        while True:
            k = stdscr.getch()
            if k in (ord("q"), ord("Q"), 27):
                break
            for y in range(fh - 1):
                for x in range(fw):
                    sx = max(0, min(fw - 1, x + random.randint(-1, 1)))
                    fire[y][x] = max(0, fire[y + 1][sx] - random.randint(0, 1))
            for y in range(fh):
                ry = y + logo_rows
                if ry >= height:
                    break
                for x in range(fw):
                    v = fire[y][x]
                    try:
                        stdscr.addch(ry, x, CHARS[v], curses.color_pair(pair(v)))
                    except curses.error:
                        pass
            stdscr.refresh()
            time.sleep(0.03)

    curses.wrapper(loop)


def run_doom(on_status=None) -> None:
    """Run DOOM. Uses terminal-doom on supported terminals, fire effect otherwise."""
    log = DOOM_DIR / "debug.log"
    DOOM_DIR.mkdir(parents=True, exist_ok=True)

    term = os.environ.get("TERM_PROGRAM", "")
    kitty = _supports_kitty_graphics()
    built = _is_built()

    with open(log, "w") as f:
        f.write(f"TERM_PROGRAM={term!r}\n")
        f.write(f"supports_kitty={kitty}\n")
        f.write(f"is_built={built}\n")
        f.write(f"DOOM_BIN={DOOM_BIN} exists={DOOM_BIN.exists()}\n")
        f.write(f"DOOM_WAD={DOOM_WAD} exists={DOOM_WAD.exists()}\n")

    if kitty:
        if not built:
            ok = _build_terminal_doom(on_status=on_status)
            with open(log, "a") as f:
                f.write(f"build result={ok}\n")
            if not ok:
                _run_fire_effect()
                return
        result = _run_terminal_doom()
        with open(log, "a") as f:
            f.write(f"terminal-doom returned={result}\n")
        if not result:
            _run_fire_effect()
    else:
        _run_fire_effect()
