#!/usr/bin/env python3
"""Claude Code status line: prints a compact line and caches the full payload
so the cockpit side panels can show live session data."""
import json, os, sys, time

CACHE = os.path.expanduser("~/.cache/claude-cockpit")
os.makedirs(CACHE, exist_ok=True)

try:
    data = json.load(sys.stdin)
except Exception:
    data = {}

data["_ts"] = time.time()
tmp = os.path.join(CACHE, "status.json.tmp")
with open(tmp, "w") as f:
    json.dump(data, f)
os.replace(tmp, os.path.join(CACHE, "status.json"))
# per-project copy so each cockpit shows its own session
import hashlib
proj = (data.get("workspace") or {}).get("project_dir") or (data.get("workspace") or {}).get("current_dir")
if proj:
    key = hashlib.md5(os.path.realpath(proj).encode()).hexdigest()[:12]
    with open(tmp, "w") as f:
        json.dump(data, f)
    os.replace(tmp, os.path.join(CACHE, f"status-{key}.json"))


def rgb(h):
    h = h.lstrip("#")
    return "\033[38;2;%d;%d;%dm" % tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


R = "\033[0m"
MAUVE, BLUE, GREEN, YELLOW, RED, DIM = (rgb(c) for c in
                                         ("cba6f7", "89b4fa", "a6e3a1", "f9e2af", "f38ba8", "6c7086"))


def pct_color(p):
    return GREEN if p < 50 else YELLOW if p < 80 else RED


parts = []
model = (data.get("model") or {}).get("display_name")
if model:
    parts.append(f"{MAUVE}\U000f06a9 {model}{R}")

ctx = data.get("context_window") or {}
used = ctx.get("used_percentage")
if used is not None:
    parts.append(f"{pct_color(used)}\U000f035b ctx {used:.0f}%{R}")

cost = (data.get("cost") or {}).get("total_cost_usd")
if cost is not None:
    parts.append(f"{GREEN} ${cost:.2f}{R}")

five = ((data.get("rate_limits") or {}).get("five_hour") or {}).get("used_percentage")
if five is not None:
    parts.append(f"{pct_color(five)}\U000f051f 5h {five:.0f}%{R}")

cwd = (data.get("workspace") or {}).get("current_dir")
if cwd:
    parts.append(f"{BLUE} {os.path.basename(cwd)}{R}")

print(f" {DIM}│{R} ".join(parts))
