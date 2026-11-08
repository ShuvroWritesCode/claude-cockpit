"""Shared rendering helpers for the cockpit panels (Catppuccin Mocha palette)."""
import os, re, shutil, sys, time


def rgb(h):
    h = h.lstrip("#")
    return "\033[38;2;%d;%d;%dm" % tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


R = "\033[0m"
B = "\033[1m"
I = "\033[3m"
MAUVE = rgb("cba6f7")
BLUE = rgb("89b4fa")
SAPPHIRE = rgb("74c7ec")
TEAL = rgb("94e2d5")
GREEN = rgb("a6e3a1")
YELLOW = rgb("f9e2af")
PEACH = rgb("fab387")
RED = rgb("f38ba8")
PINK = rgb("f5c2e7")
TEXT = rgb("cdd6f4")
SUB = rgb("a6adc8")
DIM = rgb("6c7086")
SURF = rgb("45475a")

ANSI = re.compile(r"\033\[[0-9;]*m")
CACHE = os.path.expanduser("~/.cache/claude-cockpit")


def width():
    return shutil.get_terminal_size((40, 20)).columns


def vlen(s):
    return len(ANSI.sub("", s))


def header(icon, title, color=MAUVE):
    w = width()
    label = f" {icon} {title} "
    return f"{color}{B}{label}{R}{SURF}{'─' * max(0, w - vlen(label) - 1)}{R}"


def kv(key, val, kc=SUB):
    return f"  {kc}{key:<9}{R}{TEXT}{val}{R}"


def pct_color(p):
    return GREEN if p < 50 else YELLOW if p < 80 else RED


def bar(p, w=None, color=None):
    w = w or max(8, width() - 18)
    p = max(0.0, min(100.0, p))
    full = int(round(p / 100 * w))
    c = color or pct_color(p)
    return f"{c}{'━' * full}{SURF}{'━' * (w - full)}{R}"


def human(n):
    n = float(n or 0)
    for unit in ("", "K", "M", "B"):
        if abs(n) < 1000:
            return f"{n:.0f}{unit}" if unit == "" else f"{n:.1f}{unit}"
        n /= 1000
    return f"{n:.1f}T"


def dur(seconds):
    seconds = max(0, int(seconds))
    h, m = divmod(seconds // 60, 60)
    d, h = divmod(h, 24)
    if d:
        return f"{d}d {h}h"
    return f"{h}h {m:02d}m" if h else f"{m}m"


def trim(s, w):
    """Cut to w visible columns without breaking escape sequences."""
    out, seen, i = [], 0, 0
    while i < len(s) and seen < w - 1:
        m = ANSI.match(s, i)
        if m:
            out.append(m.group())
            i = m.end()
            continue
        out.append(s[i])
        seen += 1
        i += 1
    return "".join(out) + "…" + R


def draw(lines):
    """Repaint in place without flicker."""
    w = width()
    out = ["\033[H"]
    for ln in lines:
        if vlen(ln) > w:
            ln = trim(ln, w)
        out.append(ln + "\033[K\n")
    out.append("\033[J")
    sys.stdout.write("".join(out))
    sys.stdout.flush()


def run_loop(render, interval):
    sys.stdout.write("\033[?25l\033[2J")
    try:
        while True:
            try:
                draw(render())
            except Exception as e:  # keep the panel alive
                draw([f"{RED}panel error: {e}{R}"])
            time.sleep(interval)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\033[?25h" + R)


def status_for(dir_=None):
    """Live Claude status for this cockpit's project, else the most recent one."""
    import hashlib, json
    names = []
    if dir_:
        key = hashlib.md5(os.path.realpath(dir_).encode()).hexdigest()[:12]
        names.append(f"status-{key}.json")
    names.append("status.json")
    for n in names:
        try:
            with open(os.path.join(CACHE, n)) as f:
                return json.load(f)
        except Exception:
            continue
    return {}
