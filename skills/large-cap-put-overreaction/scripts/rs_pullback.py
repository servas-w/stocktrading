#!/usr/bin/env python3
"""
rs_pullback.py - Relative-Strength Weekly-EMA Pullback + 30m Short-Term Reversal scanner
for the large-cap-put-overreaction skill (v6). Stdlib only. Never crashes on gaps.

What it answers, per ticker:
  1. STRUCTURE  - Is this a relative-strength name that has *held* a weekly EMA (9W or 21W)
                  for 10-15 weeks, and is it now pulling back INTO that EMA? (grade A/B/C/F)
  2. TRIGGER    - On 30-minute bars: after a sell-off, the FIRST green 30m candle is the marker;
                  a later (ideally the next) candle CLOSING above the marker's high = trigger;
                  the marker's low = invalidation. States: NO_SELLOFF / SELLING / WATCH /
                  TRIGGERED / STOPPED.
  3. PUT MAP    - Strike ceiling for the short put = min(next weekly support below the defended
                  EMA, spot x (1 - required cushion)). Cushion still beats delta.
  4. FILTERS    - Liquidity regime (SPY/HYG/RSP vs their 21W EMA) and earnings < 7 days.

Usage:
  python3 rs_pullback.py scan '<json>'      # json inline, a file path, or '-' for stdin
  python3 rs_pullback.py triage '{"rows":[{"t":"DE","ivr":0.57,"ivhv":1.0,"chg5":-0.075,"rsi":33,"vs21":-0.014,"vs50":0.047,"er":44}]}'
                                            # classify IV Spike Dislocation scan rows (no extra data calls)
  python3 rs_pullback.py scan file.json --json   # machine-readable output

Input:
{"asof":"2026-10-12T15:10:00Z",
 "cushion":0.15,                       # required cushion from the skill (0.15 / 0.25 / 0.30 / D-EV adj.)
 "regime":{"SPY":0.020,"HYG":-0.020,"RSP":-0.007,"QQQ":0.030},   # % vs 21W EMA as ratios (regime scan)
 "bench":{"c":[...weekly SPY closes, oldest->newest...]},          # optional, for RS vs SPY
 "names":[{"ticker":"TER","spot":390.5,"next_earnings":"2026-10-28",
           "weekly":{"c":[...],"l":[...]}  OR Robinhood bar dicts  OR [[o,h,l,c],...],
           "m30":[[ "2026-10-12T13:30:00Z", o,h,l,c,v ], ...]  OR Robinhood bar dicts}]}
Weekly needs >= 30 bars (21W EMA + warm-up); 55+ unlocks the 50W EMA. m30: last 2-3 sessions.
Pass "asof" so the in-progress weekly / 30m bar is excluded from signals (bars are left-edge UTC).
"""
import sys, json, math
from datetime import datetime, timedelta, timezone

# ---------- parsing ----------
def num(v):
    try:
        x = float(v)
        return x if math.isfinite(x) else None
    except (TypeError, ValueError):
        return None

def ts(s):
    if not s or not isinstance(s, str):
        return None
    for cand in (s.replace("Z", "+00:00"), s[:10] + "T00:00:00+00:00"):
        try:
            d = datetime.fromisoformat(cand)
            return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None

def bars(raw):
    """Robinhood bar dicts | [[t?,o,h,l,c,v?],...] | columnar {'c':[],'l':[],'h':[],'o':[],'t':[],'v':[]}"""
    out = []
    if raw is None:
        return out
    if isinstance(raw, dict) and "bars" in raw:
        raw = raw["bars"]
    if isinstance(raw, dict):
        c = raw.get("c") or []
        n = len(c)
        def col(k):
            v = raw.get(k)
            return v if isinstance(v, list) and len(v) == n else [None] * n
        o, h, l, v, t = col("o"), col("h"), col("l"), col("v"), col("t")
        for i in range(n):
            out.append(dict(t=ts(t[i]), o=num(o[i]), h=num(h[i]), l=num(l[i]), c=num(c[i]), v=num(v[i])))
    else:
        for b in raw:
            if isinstance(b, dict):
                if b.get("interpolated"):
                    continue
                out.append(dict(t=ts(b.get("begins_at") or b.get("t")),
                                o=num(b.get("open_price", b.get("o"))), h=num(b.get("high_price", b.get("h"))),
                                l=num(b.get("low_price", b.get("l"))), c=num(b.get("close_price", b.get("c"))),
                                v=num(b.get("volume", b.get("v")))))
            elif isinstance(b, (list, tuple)) and len(b) >= 4:
                t = None
                if isinstance(b[0], str):
                    t, b = ts(b[0]), b[1:]
                if len(b) < 4:
                    continue
                out.append(dict(t=t, o=num(b[0]), h=num(b[1]), l=num(b[2]), c=num(b[3]),
                                v=num(b[4]) if len(b) > 4 else None))
    out = [x for x in out if x["c"] is not None]
    for x in out:  # fill gaps so nothing crashes
        x["o"] = x["o"] if x["o"] is not None else x["c"]
        x["h"] = x["h"] if x["h"] is not None else max(x["o"], x["c"])
        x["l"] = x["l"] if x["l"] is not None else min(x["o"], x["c"])
    return out

def ema(vals, n):
    out = [None] * len(vals)
    if len(vals) < n:
        return out
    k = 2.0 / (n + 1)
    e = sum(vals[:n]) / n
    out[n - 1] = e
    for i in range(n, len(vals)):
        e = vals[i] * k + e * (1 - k)
        out[i] = e
    return out

def pct(x, dp=1):
    return "n/a" if x is None else f"{x*100:+.{dp}f}%"

def money(x):
    return "n/a" if x is None else f"{x:,.2f}"

# ---------- regime ----------
def regime(r):
    """Liquidity-regime PROXY: index + credit + breadth vs their 21W EMA (ratios)."""
    if not r:
        return "UNVERIFIED", "regime not supplied -> treat as CAUTION"
    spy, hyg, rsp = num(r.get("SPY")), num(r.get("HYG")), num(r.get("RSP"))
    if spy is None:
        return "UNVERIFIED", "SPY missing -> treat as CAUTION"
    if spy < 0 and (hyg is None or hyg < 0):
        return "RISK-OFF", f"SPY {pct(spy)} & HYG {pct(hyg)} vs 21W: supports fail more often"
    weak = [k for k, v in (("HYG", hyg), ("RSP", rsp)) if v is not None and v < 0]
    if spy < 0 or weak:
        return "CAUTION", "below 21W: " + ", ".join((["SPY"] if spy < 0 else []) + weak)
    return "RISK-ON", f"SPY {pct(spy)}, HYG {pct(hyg)}, RSP {pct(rsp)} vs 21W"

# ---------- weekly structure ----------
def hold_stats(closes, lows, e, look=15):
    idx = [i for i in range(len(closes)) if e[i] is not None]
    if not idx:
        return None
    consec = 0
    for i in reversed(idx):
        if closes[i] > e[i]:
            consec += 1
        else:
            break
    last = idx[-look:]
    above = sum(1 for i in last if closes[i] > e[i])
    tests = sum(1 for i in last if lows[i] <= e[i] < closes[i])  # wick tagged EMA, closed above = buyer showed up
    return dict(consec=consec, above=above, window=len(last), tests=tests)

def align(series, n):
    """End-align a supplied EMA series (oldest->newest, one value per completed week) to n closes."""
    vals = [num(v) for v in series]
    vals = vals[-n:]
    return [None] * (n - len(vals)) + vals

def weekly(w, spot, asof, bench, cushion, sup=None, band=0.03, brk=0.03):
    r = dict(ok=False)
    sup = sup or {}
    partial = bool(asof and w and w[-1]["t"] and w[-1]["t"] + timedelta(days=7) > asof)
    done = w[:-1] if partial else w
    cl = [b["c"] for b in done]
    lo = [b["l"] for b in done]
    if spot is None:
        spot = w[-1]["c"] if w else None
    r["spot"] = spot
    supplied = isinstance(sup.get("e9"), list) and isinstance(sup.get("e21"), list)
    need = 15 if supplied else 30
    if len(cl) < need or spot is None:
        r["why"] = (f"need >= {need} completed weekly bars (have {len(cl)})"
                    + ("" if supplied else " - or pass e9/e21 series from get_equity_technical_indicators"))
        return r
    if supplied:   # server-computed EMAs (warm-up handled upstream) -> only ~16 weekly bars needed
        e9, e21 = align(sup["e9"], len(cl)), align(sup["e21"], len(cl))
        e50v = sup.get("e50")
        e50 = align(e50v, len(cl)) if isinstance(e50v, list) else [None] * (len(cl) - 1) + [num(e50v)]
    else:
        e9, e21, e50 = ema(cl, 9), ema(cl, 21), ema(cl, 50)
    E9, E21, E50 = e9[-1], e21[-1], e50[-1]
    if E9 is None or E21 is None:
        r["why"] = "EMA series empty or misaligned"
        return r
    r["ema_src"] = "supplied (server)" if supplied else "computed"
    d9, d21 = spot / E9 - 1, spot / E21 - 1
    h9, h21 = hold_stats(cl, lo, e9), hold_stats(cl, lo, e21)
    rising21 = e21[-5] is not None and e21[-1] > e21[-5]
    stack = E9 > E21 and rising21 and (E50 is None or E21 > E50)
    ret13 = spot / cl[-13] - 1 if len(cl) >= 13 else None
    rs13 = None   # completed-week vs completed-week, both 13 weeks (pass bench as COMPLETED weekly closes)
    if bench and len(bench) >= 14 and len(cl) >= 14:
        rs13 = (cl[-1] / cl[-14] - 1) - (bench[-1] / bench[-14] - 1)
    swing13 = min(lo[-13:])

    # where is price relative to the weekly EMAs?
    if d21 < -brk:
        zone, defended = "BROKEN", None          # sliced through (STX case)
    elif abs(d9) <= band and abs(E9 / E21 - 1) <= band:
        zone, defended = "9W/21W CLUSTER", "21W"
    elif abs(d9) <= band:
        zone, defended = "AT 9W", "9W"
    elif abs(d21) <= band:
        zone, defended = "AT 21W", "21W"
    elif d9 > band:
        zone, defended = "EXTENDED", None        # no pullback yet
    else:
        zone, defended = "BETWEEN 9W-21W", "21W"  # in transit to 21W

    # article: if price keeps breaking above/below the 9W, the 9W is not a reliable support
    if defended == "9W" and h9 and h9["consec"] < 6 and h21 and h21["consec"] >= 6:
        zone, defended = "9W UNRELIABLE", "21W"
    hs = h9 if defended == "9W" else h21
    if defended == "9W":
        support, sup_name = E21, "21W EMA"
    elif E50 is not None:
        support, sup_name = E50, "50W EMA"
    else:
        support, sup_name = swing13, "13W swing low (50W EMA n/a)"

    # grade: the longer the hold, the more likely a responsive buyer
    if zone == "BROKEN" or E9 < E21:
        grade = "F"
    elif hs and hs["consec"] >= 10 and hs["above"] >= 13 and stack and (rs13 is None or rs13 > 0):
        grade = "A"
    elif hs and hs["consec"] >= 6 and hs["above"] >= 10 and E9 > E21:
        grade = "B"
    else:
        grade = "C"
    ceiling = min(support, spot * (1 - cushion))
    r.update(ok=True, partial_week_excluded=partial, E9=E9, E21=E21, E50=E50, d9=d9, d21=d21,
             h9=h9, h21=h21, stack=stack, rising21=rising21, ret13=ret13, rs13=rs13,
             zone=zone, defended=defended, grade=grade, support=support, sup_name=sup_name,
             swing13=swing13, ceiling=ceiling, cushion=cushion,
             defended_level=(E9 if defended == "9W" else E21 if defended else None),
             levels=[E9, E21] if zone == "9W/21W CLUSTER" else None)
    return r

# ---------- 30m short-term reversal ----------
def reversal(m, asof, ema_level=None, drop=0.015, peak_bars=8, noise=0.10, levels=None):
    r = dict(state="NO_DATA")
    if not m:
        return r
    notes = []
    if asof and m[-1]["t"] and m[-1]["t"] + timedelta(minutes=30) > asof:
        m = m[:-1]
        notes.append("in-progress bar excluded")
    vols = sorted(b["v"] for b in m if b["v"])
    med = vols[len(vols) // 2] if vols else None
    if med:
        n0 = len(m)
        m = [b for b in m if b["v"] is None or b["v"] >= noise * med]
        if len(m) < n0:
            notes.append(f"{n0-len(m)} odd-lot/glitch print(s) dropped")
    if len(m) < 3:
        r.update(state="NO_DATA", notes=notes)
        return r

    state, mk, entry_i, sell_peak, history = "NO_SELLOFF", None, None, None, []
    for i, b in enumerate(m):
        red, green = b["c"] < b["o"], b["c"] > b["o"]
        prior = m[max(0, i - peak_bars):i]
        peak = max([x["h"] for x in prior]) if prior else b["h"]
        dd = b["l"] / peak - 1
        if state in ("NO_SELLOFF", "STOPPED", "INVALID"):
            if red and dd <= -drop:
                state, sell_peak = "SELLING", peak
            continue
        if state == "SELLING":
            if green:
                state, mk = "WATCH", i       # first green 30m close after the downturn = marker
            continue
        if state == "WATCH":
            if b["l"] < m[mk]["l"]:          # downturn resumed through the marker low before entry
                history.append(("INVALID", mk))
                state, mk = ("SELLING" if red else "INVALID"), None
                if state == "SELLING":
                    sell_peak = peak
                continue
            if b["c"] > m[mk]["h"]:
                state, entry_i = "TRIGGERED", i
            continue
        if state == "TRIGGERED":
            if b["c"] < m[mk]["l"]:
                history.append(("STOPPED", mk))
                state = "STOPPED"
                if red and dd <= -drop:
                    state, sell_peak = "SELLING", peak
            continue

    if state == "SELLING":
        mk = None
    r.update(state=state, notes=notes, bars=len(m), prior=[h[0] for h in history])
    if mk is not None:
        M = m[mk]
        r.update(marker_time=M["t"].strftime("%m-%d %H:%MZ") if M["t"] else f"bar {mk}",
                 marker_high=M["h"], marker_low=M["l"], selloff_peak=sell_peak,
                 selloff=(M["l"] / sell_peak - 1) if sell_peak else None)
        cands = [x for x in (levels or [ema_level]) if x]
        if cands:   # marker low formed at (one of) the defended weekly EMA(s)
            off = min((M["l"] / x - 1 for x in cands), key=abs)
            r["confluence"] = -0.03 <= off <= 0.025
            r["marker_vs_ema"] = off
    if entry_i is not None and mk is not None:
        E = m[entry_i]
        r.update(entry_time=E["t"].strftime("%m-%d %H:%MZ") if E["t"] else f"bar {entry_i}",
                 entry=E["c"], stop=m[mk]["l"], stop_dist=m[mk]["l"] / E["c"] - 1,
                 bars_to_trigger=entry_i - mk,
                 trig_rvol=(E["v"] / med) if (E["v"] and med) else None,
                 follow=max(x["h"] for x in m[entry_i:]) / E["c"] - 1, last=m[-1]["c"])
        if E["t"] and m[-1]["t"]:
            sessions = len({x["t"].date() for x in m[entry_i:] if x["t"]}) - 1
            r["sessions_since_trigger"] = sessions
            if state == "TRIGGERED" and sessions > 1:
                r["state"] = "TRIGGERED-STALE"
    return r

# ---------- verdict ----------
def verdict(w, t, reg, er_days):
    if not w.get("ok"):
        return "UNVERIFIED", w.get("why", "weekly data missing")
    g, z = w["grade"], w["zone"]
    if g == "F":
        return "VOID", "weekly structure broken - EMA did not hold (no RS-pullback entry)"
    if er_days is not None and 0 <= er_days < 7:
        return "BLOCKED-ER", f"earnings in {er_days}d - binary event can break the technical setup"
    if reg == "RISK-OFF":
        return "STAND DOWN", "negative-liquidity proxy - supports fail more often"
    if z == "9W UNRELIABLE":
        return "WAIT", (f"9W keeps breaking (held only {w['h9']['consec']} wk); real support = 21W "
                        f"{money(w['E21'])} ({pct(-w['d21'])} away)")
    if z == "EXTENDED":
        return "WAIT", f"{pct(w['d9'])} above 9W - no pullback yet; alert at 9W {money(w['E9'])}"
    s = t.get("state")
    if s == "TRIGGERED" and z == "BETWEEN 9W-21W":
        return "WATCH", "30m trigger fired mid-air between the EMAs - no weekly support under it; wait for the 21W test"
    if s == "TRIGGERED":
        lead = "READY" if g in ("A", "B") else "READY-C"
        tail = " (spread-only, half size)" if reg in ("CAUTION", "UNVERIFIED") else ""
        conf = "" if t.get("confluence", True) else " - marker not at weekly EMA (lower confluence)"
        return lead, f"30m reversal confirmed at {z}{tail}{conf}"
    if s == "TRIGGERED-STALE":
        return "WATCH", f"trigger is {t.get('sessions_since_trigger')} sessions old - wait for a fresh marker at {z}"
    if s == "STOPPED":
        return "FAILED-TODAY", "30m reversal stopped out - level may be slicing; wait for a new marker"
    if s in ("WATCH", "SELLING"):
        return "WATCH", f"in {z}; 30m {s.lower()} - wait for close > marker high"
    if z == "BETWEEN 9W-21W":
        return "WAIT", f"9W lost, 21W {money(w['E21'])} is the next test"
    return "WATCH", f"in {z}; no 30m sell-off/marker yet"

RANK = {"READY": 0, "READY-C": 1, "WATCH": 2, "FAILED-TODAY": 3, "WAIT": 4, "BLOCKED-ER": 5,
        "STAND DOWN": 6, "VOID": 7, "UNVERIFIED": 8}

def scan(x, as_json=False):
    asof = ts(x.get("asof"))
    asof_note = None
    if asof is None:
        asof = datetime.now(timezone.utc)
        asof_note = "asof not supplied -> using container clock (UTC); in-progress bars may be mis-handled"
    cushion = num(x.get("cushion")) or 0.15
    reg, reg_why = regime(x.get("regime"))
    b = x.get("bench")
    bench = [k["c"] for k in bars(b)] if b else None
    rows = []
    for n in x.get("names", []):
        tk = n.get("ticker", "?")
        w = weekly(bars(n.get("weekly")), num(n.get("spot")), asof, bench, num(n.get("cushion")) or cushion,
                   sup={k: n.get(k) for k in ("e9", "e21", "e50")})
        t = (reversal(bars(n.get("m30")), asof, w.get("defended_level"), levels=w.get("levels"))
             if n.get("m30") else dict(state="NO_DATA"))
        er = n.get("next_earnings")
        er_days = None
        if er and asof:
            d = ts(er)
            er_days = (d.date() - asof.date()).days if d else None
        v, why = verdict(w, t, reg, er_days)
        rows.append(dict(ticker=tk, verdict=v, why=why, er_days=er_days, w=w, t=t))
    rows.sort(key=lambda r: (RANK.get(r["verdict"], 9), {"A": 0, "B": 1, "C": 2, "F": 3}.get(r["w"].get("grade"), 4)))

    if as_json:
        def clean(o):
            if isinstance(o, dict):
                return {k: clean(v) for k, v in o.items()}
            if isinstance(o, (list, tuple)):
                return [clean(v) for v in o]
            if isinstance(o, float):
                return round(o, 4)
            return o
        print(json.dumps(clean(dict(regime=reg, regime_why=reg_why, rows=rows)), default=str))
        return

    print(f"REGIME: {reg} - {reg_why}")
    if asof_note:
        print("NOTE: " + asof_note)
    print(f"{'Tkr':<6}{'Verdict':<13}{'Gr':<3}{'Zone':<16}{'Run/In15   ':<11}{'vs9W':>7}{'vs21W':>7}{'RS13':>7}  {'30m':<10}{'ER':>4}")
    for r in rows:
        w, t = r["w"], r["t"]
        hs = (w.get("h9") if w.get("defended") == "9W" else w.get("h21")) if w.get("ok") else None
        held = f"{hs['consec']}/{hs['above']}" if hs else "n/a"
        print(f"{r['ticker']:<6}{r['verdict']:<13}{w.get('grade','-'):<3}{w.get('zone','n/a'):<16}{held:<11}"
              f"{pct(w.get('d9')):>7}{pct(w.get('d21')):>7}{pct(w.get('rs13') if w.get('rs13') is not None else w.get('ret13'),0):>7}  "
              f"{t.get('state','-'):<10}{(str(r['er_days'])+'d') if r['er_days'] is not None else 'n/a':>4}")
    print()
    for r in rows:
        w, t = r["w"], r["t"]
        print(f"[{r['ticker']}] {r['verdict']}: {r['why']}")
        if w.get("ok"):
            e50 = f" | 50W {money(w['E50'])}" if w.get("E50") else ""
            rs = "RS13 vs SPY" if w.get("rs13") is not None else "13W ret (no bench)"
            print(f"  weekly: spot {money(w['spot'])} | 9W {money(w['E9'])} | 21W {money(w['E21'])}{e50} | "
                  f"stack {'yes' if w['stack'] else 'no'} | {rs} {pct(w.get('rs13') if w.get('rs13') is not None else w.get('ret13'))}"
                  f"{' | partial week excluded' if w['partial_week_excluded'] else ''}")
            for lab, hs in (("9W", w["h9"]), ("21W", w["h21"])):
                if hs:
                    print(f"  held {lab}: {hs['consec']} consecutive weekly closes above, {hs['above']}/{hs['window']} in window, {hs['tests']} wick-tests held")
            if r["verdict"] not in ("VOID", "UNVERIFIED"):
                print(f"  PUT MAP: short strike <= {money(w['ceiling'])} = min(next support {w['sup_name']} {money(w['support'])}, "
                      f"spot x (1-{w['cushion']:.0%}) {money(w['spot']*(1-w['cushion']))}) -> then pick delta -0.10/-0.15 at/below it")
        if t.get("state") not in (None, "NO_DATA"):
            line = f"  30m: {t['state']}"
            if t.get("marker_low") is not None:
                line += (f" | marker {t['marker_time']} H {money(t['marker_high'])} L {money(t['marker_low'])}"
                         f" (sell-off {pct(t.get('selloff'))})")
                if "confluence" in t:
                    line += f" | marker vs weekly EMA {pct(t['marker_vs_ema'])} {'CONFLUENCE' if t['confluence'] else ''}"
            if t.get("entry") is not None:
                rv = f", vol {t['trig_rvol']:.1f}x median" if t.get("trig_rvol") else ""
                line += (f" | trigger {t['entry_time']} close {money(t['entry'])}{rv}, stop {money(t['stop'])} ({pct(t['stop_dist'])}),"
                         f" follow-through {pct(t['follow'])}, last {money(t['last'])}")
            if t.get("prior"):
                line += f" | earlier markers: {', '.join(t['prior'])}"
            print(line)
            if t.get("notes"):
                print("  note: " + "; ".join(t["notes"]))
        elif r["verdict"] in ("WATCH",):
            print("  30m: not pulled - fetch 30minute bars (last 2-3 sessions) to check the trigger")

# ---------- triage of the IV Spike Dislocation scan ----------
COLMAP = {"ivr": ("IV rank (RH)",), "ivhv": ("IV30/HV30",), "chg5": ("5D chg",), "rsi": ("RSI 14D",),
          "vs21": ("% vs 21W EMA",), "vs50": ("% vs 50W EMA",), "off_high": ("Off 52W high",),
          "er": ("Days to ER",), "last": ("Last",), "mcap": ("Market cap",)}

def tri_row(r):
    """Accept compact {"t","ivr","ivhv",...} or a Robinhood scan row {"ticker","columns":{display: value}}."""
    if "columns" in r:
        c = r["columns"]
        o = {"t": r.get("ticker") or c.get("Symbol")}
        for k, names in COLMAP.items():
            o[k] = next((num(c.get(n)) for n in names if c.get(n) not in (None, "")), None)
        return o
    o = {k: num(r.get(k)) for k in COLMAP}
    o["t"] = r.get("t") or r.get("ticker")
    return o

def triage(x, as_json=False):
    out = []
    for raw in x.get("rows", []):
        r = tri_row(raw)
        vs21, vs50, ivr, ivhv = r["vs21"], r["vs50"], r["ivr"], r["ivhv"]
        if vs50 is not None and vs50 < -0.05:
            cls, step = "BROKEN", "below the 50W: sell-off triage first (structural -> REJECT); IV gate only if transient"
        elif (vs21 is not None and -0.03 <= vs21 <= 0.03) or (vs50 is not None and -0.03 <= vs50 <= 0.03):
            cls, step = "EMA-FLUSH", "flushed INTO a weekly EMA -> IV gate + RS overlay (weeks held, 30m trigger)"
        elif vs21 is not None and vs21 > 0.10:
            cls, step = "EXTENDED", "dropped but still far above the 21W -> IV gate + lc; strike also <= 21W EMA"
        else:
            cls, step = "MID-AIR", "between EMAs, no support under price -> IV gate; strike <= next weekly EMA below"
        score = (ivr or 0) * 100
        score += {"EMA-FLUSH": 20, "EXTENDED": 10, "MID-AIR": 0, "BROKEN": -15}[cls]
        flags = []
        if ivhv is None:
            flags.append("IV/HV n/a")
        elif ivhv < 0.8:
            score -= 25
            flags.append(f"IV/HV {ivhv:.2f}: realized > implied, premium NOT rich")
        elif ivhv < 1.0:
            score -= 5
            flags.append(f"IV/HV {ivhv:.2f}: thin edge")
        else:
            score += 5
        if r["rsi"] is not None and r["rsi"] < 30:
            score += 5
            flags.append(f"RSI {r['rsi']:.0f} capitulation")
        if r["er"] is not None and r["er"] < 90:
            flags.append(f"ER {int(r['er'])}d: HAZARD unless expiry precedes it")
        out.append(dict(t=r["t"], cls=cls, score=round(score), step=step, flags=flags, r=r))
    out.sort(key=lambda o: -o["score"])
    if as_json:
        print(json.dumps(out, default=str))
        return
    print(f"{'Tkr':<6}{'Score':>6}  {'Class':<10}{'IVR':>5}{'IV/HV':>7}{'5D':>7}{'vs21W':>7}{'vs50W':>7}{'ER':>5}")
    for o in out:
        r = o["r"]
        print(f"{o['t']:<6}{o['score']:>6}  {o['cls']:<10}{(r['ivr'] or 0)*100:>5.0f}"
              f"{(r['ivhv'] if r['ivhv'] is not None else float('nan')):>7.2f}{pct(r['chg5'],0):>7}{pct(r['vs21'],0):>7}"
              f"{pct(r['vs50'],0):>7}{(str(int(r['er']))+'d') if r['er'] is not None else 'n/a':>5}")
    print()
    picked = 0
    for o in out:
        nxt = picked < 3 and o["cls"] != "BROKEN"
        picked += nxt
        tag = "-> NEXT: " if nxt else "   "
        print(f"{tag}{o['t']} [{o['cls']}] {o['step']}" + (f" | {'; '.join(o['flags'])}" if o["flags"] else ""))
    print("\nRH ivRank is a pre-filter; IBKR IVP decides the gate. Top 3 non-BROKEN names go to the IV gate.")

def load(a):
    if a == "-":
        return json.load(sys.stdin)
    a = a.strip()
    if a.startswith("{"):
        return json.loads(a)
    with open(a) as f:
        return json.load(f)

if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] not in ("scan", "triage"):
        print(__doc__)
        sys.exit(0)
    try:
        {"scan": scan, "triage": triage}[sys.argv[1]](load(sys.argv[2]), "--json" in sys.argv)
    except Exception as e:  # never crash the workflow
        print(f"rs_pullback: input error - {e}. Check JSON shape (see --help).")
