#!/usr/bin/env python3
"""Right sidebar: the project Claude is working in — git state, changes, commits, todos."""
import json, os, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: E402,F401,F403

START = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.getcwd()


def git(*args, cwd):
    try:
        r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=5)
        return r.stdout.rstrip() if r.returncode == 0 else None
    except Exception:
        return None


def project_dir():
    return START


STATUS_COLORS = {"M": YELLOW, "A": GREEN, "D": RED, "R": BLUE, "?": DIM, "U": PEACH}


def render():
    cwd = project_dir()
    w = width()
    L = [header("\U000f024b", "PROJECT", BLUE)]
    L.append(f"  {TEXT}{B}{os.path.basename(cwd) or cwd}{R}")
    home = os.path.expanduser("~")
    L.append(f"  {DIM}{cwd.replace(home, '~', 1)}{R}")
    L.append("")

    branch = git("branch", "--show-current", cwd=cwd)
    if branch is None:
        L.append(f"  {DIM}{I}not a git repository{R}")
        return L
    ab = git("rev-list", "--left-right", "--count", "@{upstream}...HEAD", cwd=cwd)
    sync = ""
    if ab:
        behind, ahead = ab.split()
        sync = f"  {GREEN}↑{ahead}{R} {RED}↓{behind}{R}"
    L.append(header("\U000f062c", "GIT", PINK))
    L.append(f"  {PINK} {branch or '(detached)'}{R}{sync}")

    status = (git("status", "--porcelain", cwd=cwd) or "").splitlines()
    stash = git("stash", "list", cwd=cwd)
    nstash = len(stash.splitlines()) if stash else 0
    L.append(f"  {SUB}{len(status)} changed{R}" + (f"  {DIM}{nstash} stashed{R}" if nstash else ""))
    for line in status[:12]:
        code, path = line[:2], line[3:]
        c = STATUS_COLORS.get(code.strip()[:1] or "?", TEXT)
        L.append(f"  {c}{code}{R} {TEXT}{path[: w - 7]}{R}")
    if len(status) > 12:
        L.append(f"  {DIM}… {len(status) - 12} more{R}")
    L.append("")

    L.append(header("\U000f0718", "RECENT COMMITS", SAPPHIRE))
    log = git("log", "-8", "--pretty=format:%h\x1f%s\x1f%cr", cwd=cwd) or ""
    for row in log.splitlines():
        h, subj, when = (row.split("\x1f") + ["", "", ""])[:3]
        when = when.replace(" ago", "").replace("minutes", "m").replace("minute", "m") \
                   .replace("hours", "h").replace("hour", "h").replace("days", "d") \
                   .replace("day", "d").replace("weeks", "w").replace("months", "mo")
        room = max(10, w - len(h) - len(when) - 6)
        L.append(f"  {YELLOW}{h}{R} {TEXT}{subj[:room]}{R} {DIM}{when}{R}")
    L.append("")

    todos = git("grep", "-n", "-I", "-E", r"\b(TODO|FIXME|HACK)\b", "--", ".", ":!*.lock",
                ":!node_modules", cwd=cwd) or ""
    rows = todos.splitlines()
    L.append(header("\U000f0133", f"TODO / FIXME  {len(rows)}", GREEN))
    for row in rows[:8]:
        parts = row.split(":", 2)
        if len(parts) == 3:
            f, n, txt = parts
            loc = f"{os.path.basename(f)}:{n}"
            L.append(f"  {BLUE}{loc}{R} {SUB}{txt.strip()[: max(10, w - len(loc) - 5)]}{R}")
    return L


if __name__ == "__main__":
    run_loop(render, 3)
