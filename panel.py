#!/usr/bin/env python3
"""Left sidebar: Claude account, live session, token burn, and Mac system."""
import json, os, platform, shutil, subprocess, sys, threading, time
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: E402,F401,F403

usage = {"block": None, "today": None, "week": None, "err": None, "at": 0}


def sh(cmd, timeout=60):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout).stdout
    except Exception:
        return ""


def ccusage_worker():
    ccu = shutil.which("ccusage") or "ccusage"
    while True:
        try:
            today = datetime.now().strftime("%Y%m%d")
            week = datetime.fromtimestamp(time.time() - 6 * 86400).strftime("%Y%m%d")
            b = json.loads(sh([ccu, "blocks", "--active", "--json", "--offline"]) or "{}")
            t = json.loads(sh([ccu, "daily", "--json", "--offline", "--since", today]) or "{}")
            wk = json.loads(sh([ccu, "daily", "--json", "--offline", "--since", week]) or "{}")
            usage.update(block=(b.get("blocks") or [None])[0], today=t.get("totals"),
                         week=wk.get("totals"), err=None, at=time.time())
        except Exception as e:
            usage["err"] = str(e)
        time.sleep(20)


def account():
    try:
        with open(os.path.expanduser("~/.claude.json")) as f:
            return json.load(f).get("oauthAccount") or {}
    except Exception:
        return {}


PROJECT = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.getcwd()


def live_status():
    return status_for(PROJECT)


def ts(v):
    """Accept epoch seconds/ms or ISO strings."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return v / 1000 if v > 1e12 else v
    try:
        return datetime.fromisoformat(str(v).replace("Z", "+00:00")).timestamp()
    except Exception:
        return None


# ---------- Mac system ----------
_static = {}


def static_info():
    if not _static:
        _static["chip"] = sh(["sysctl", "-n", "machdep.cpu.brand_string"]).strip()
        _static["os"] = "macOS " + platform.mac_ver()[0]
        _static["host"] = platform.node().split(".")[0]
        _static["mem"] = int(sh(["sysctl", "-n", "hw.memsize"]).strip() or 0)
        _static["ncpu"] = os.cpu_count() or 1
        boot = sh(["sysctl", "-n", "kern.boottime"])
        try:
            _static["boot"] = int(boot.split("sec =")[1].split(",")[0])
        except Exception:
            _static["boot"] = None
    return _static


def mem_used_pct():
    out = sh(["vm_stat"])
    pages = {}
    for line in out.splitlines()[1:]:
        if ":" in line:
            k, v = line.split(":", 1)
            pages[k.strip()] = int(v.strip().rstrip(".") or 0)
    size = 16384
    if "page size of" in out:
        size = int(out.split("page size of")[1].split()[0])
    used = (pages.get("Pages active", 0) + pages.get("Pages wired down", 0)
            + pages.get("Pages occupied by compressor", 0)) * size
    total = static_info()["mem"] or 1
    return used / total * 100, used, total


def cpu_pct():
    out = sh(["ps", "-A", "-o", "%cpu="])
    total = sum(float(x) for x in out.split() if x.replace(".", "", 1).isdigit())
    return min(100.0, total / static_info()["ncpu"])


def battery():
    out = sh(["pmset", "-g", "batt"])
    for line in out.splitlines():
        if "%" in line:
            pct = line.split("\t")[-1].split(";")[0].strip()
            state = line.split(";")[1].strip() if ";" in line else ""
            return pct, state
    return None, None


def claude_procs():
    """Group running Claude processes: [(label, count, pid_list, rss_mb, oldest_etime)]."""
    out = sh(["ps", "-axo", "pid=,etime=,rss=,command="])
    groups = {}
    for line in out.splitlines():
        parts = line.split(None, 3)
        if len(parts) < 4:
            continue
        pid, et, rss, cmd = parts
        argv0 = cmd.split(" --")[0].split()[0] if cmd.split() else ""
        if "--chrome-native-host" in cmd and os.path.basename(argv0) == "claude":
            key = "chrome bridge"
        elif os.path.basename(argv0) == "claude":
            key = "claude code"
        elif "/Claude.app/" in cmd:
            key = "desktop app"
        else:
            continue
        g = groups.setdefault(key, {"n": 0, "pids": [], "rss": 0, "et": et})
        g["n"] += 1
        g["pids"].append(pid)
        g["rss"] += int(rss or 0) / 1024
    order = ["claude code", "chrome bridge", "desktop app"]
    return [(k, groups[k]["n"], groups[k]["pids"], groups[k]["rss"], groups[k]["et"])
            for k in order if k in groups]


# ---------- render ----------
def render():
    L = []
    a = account()
    L.append(header("\U000f06a9", "CLAUDE ACCOUNT"))
    L.append(kv("user", a.get("displayName") or a.get("fullName") or "—"))
    L.append(kv("email", a.get("emailAddress", "—")))
    plan = a.get("planDisplayName") or a.get("organizationType") or "—"
    tier = (a.get("organizationRateLimitTier") or "").replace("default_claude_", "").replace("_", " ")
    L.append(kv("plan", f"{MAUVE}{B}{plan}{R}{DIM}  {tier}{R}"))
    L.append(kv("role", a.get("organizationRole", "—")))
    L.append("")

    s = live_status()
    L.append(header("\U000f0c8a", "LIVE SESSION", BLUE))
    if s:
        age = time.time() - s.get("_ts", 0)
        live = f"{GREEN}● live{R}" if age < 120 else f"{DIM}○ idle {dur(age)}{R}"
        L.append(kv("model", f"{(s.get('model') or {}).get('display_name', '—')}  {live}"))
        cost = s.get("cost") or {}
        L.append(kv("session", f"${cost.get('total_cost_usd', 0):.2f}  {DIM}"
                               f"{dur(cost.get('total_duration_ms', 0) / 1000)}  "
                               f"{GREEN}+{cost.get('total_lines_added', 0)}{DIM}/"
                               f"{RED}-{cost.get('total_lines_removed', 0)}{R}"))
        ctx = s.get("context_window") or {}
        if ctx.get("used_percentage") is not None:
            p = ctx["used_percentage"]
            L.append(kv("context", f"{pct_color(p)}{p:.0f}%{R} {DIM}of {human(ctx.get('context_window_size'))}{R}"))
            L.append("  " + bar(p))
        rl = s.get("rate_limits") or {}
        for key, label in (("five_hour", "5h limit"), ("seven_day", "week")):
            lim = rl.get(key) or {}
            if lim.get("used_percentage") is not None:
                p = lim["used_percentage"]
                reset = ts(lim.get("resets_at"))
                rs = f" {DIM}resets {dur(reset - time.time())}{R}" if reset else ""
                L.append(kv(label, f"{pct_color(p)}{p:.0f}%{R}{rs}"))
                L.append("  " + bar(p))
    else:
        L.append(f"  {DIM}{I}waiting for Claude Code status line…{R}")
    L.append("")

    L.append(header("\U000f0238", "TOKEN BURN", PEACH))
    b = usage["block"]
    if b:
        br = b.get("burnRate") or {}
        start, end = ts(b.get("startTime")), ts(b.get("endTime"))
        L.append(kv("5h block", f"{human(b.get('totalTokens'))} tok  {GREEN}${b.get('costUSD', 0):.2f}{R}"))
        L.append(kv("burn", f"{PEACH}{human(br.get('tokensPerMinute'))}/min{R}  "
                            f"{DIM}${br.get('costPerHour', 0):.2f}/h{R}"))
        if start and end:
            el = (time.time() - start) / (end - start) * 100
            L.append(kv("window", f"{dur(end - time.time())} left"))
            L.append("  " + bar(el, color=SAPPHIRE))
        pj = b.get("projection") or {}
        if pj:
            L.append(kv("forecast", f"{human(pj.get('totalTokens'))} tok  ${pj.get('totalCost', 0):.2f}"))
    elif usage["at"]:
        L.append(f"  {DIM}no active 5h block{R}")
    else:
        L.append(f"  {DIM}{I}loading ccusage…{R}")
    for name, key in (("today", "today"), ("7 days", "week")):
        t = usage[key]
        if t:
            L.append(kv(name, f"{human(t.get('totalTokens'))} tok  {GREEN}${t.get('totalCost', 0):.2f}{R}"))
    L.append("")

    st = static_info()
    L.append(header("\U000f0379", "SYSTEM", TEAL))
    L.append(kv("host", f"{st['host']}  {DIM}{st['os']}{R}"))
    L.append(kv("chip", f"{st['chip']}  {DIM}{st['ncpu']} cores{R}"))
    c = cpu_pct()
    L.append(kv("cpu", f"{pct_color(c)}{c:4.0f}%{R}  {DIM}load {' '.join(f'{x:.2f}' for x in os.getloadavg())}{R}"))
    L.append("  " + bar(c))
    mp, mu, mt = mem_used_pct()
    L.append(kv("memory", f"{pct_color(mp)}{mp:4.0f}%{R}  {DIM}{mu / 2**30:.1f}/{mt / 2**30:.0f} GB{R}"))
    L.append("  " + bar(mp))
    du = shutil.disk_usage("/System/Volumes/Data" if os.path.exists("/System/Volumes/Data") else "/")
    dp = du.used / du.total * 100
    L.append(kv("disk", f"{pct_color(dp)}{dp:4.0f}%{R}  {DIM}{du.free / 2**30:.0f} GB free{R}"))
    bp, bs = battery()
    if bp:
        L.append(kv("battery", f"{bp}  {DIM}{bs}{R}"))
    if st.get("boot"):
        L.append(kv("uptime", dur(time.time() - st["boot"])))
    cp = claude_procs()
    L.append("")
    L.append(header("\U000f06a9", f"CLAUDE PROCS ({sum(c[1] for c in cp)})", PINK))
    for label, n, pids, rss, et in cp:
        pid_s = ",".join(pids[:2]) + ("…" if len(pids) > 2 else "")
        L.append(f"  {TEXT}{label:<14}{R}{GREEN}{n:>2}{R} {DIM}{rss:>5.0f}MB  pid {pid_s}{R}")
    L.append("")
    L.append(f"  {DIM}{datetime.now().strftime('%a %d %b  %H:%M:%S')}{R}")
    return L


if __name__ == "__main__":
    threading.Thread(target=ccusage_worker, daemon=True).start()
    run_loop(render, 2)
