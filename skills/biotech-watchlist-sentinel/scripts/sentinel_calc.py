"""Deterministic math for the Biotech Watchlist Sentinel (Claude version).

Stdlib only, no network. Import and call, or run as a CLI with one JSON
object as the argument (or on stdin):

    python3 sentinel_calc.py price    '{"bars": [...], "xbi_change_pct": -0.6}'
    python3 sentinel_calc.py overlay  '{"as_of": "2026-10-29", "event_date": "2026-11-22", "expiries": [...]}'
    python3 sentinel_calc.py skew     '{"spot": 6.1, "front": [...], "back": [...]}'
    python3 sentinel_calc.py contract '{"spot": 6.1, "dte": 79, "puts": [...]}'
    python3 sentinel_calc.py assess   '{"ivp52": 0.71, ...}'

Contracts are dicts: {type: put|call, strike, bid, ask, iv, delta, oi, volume}
with iv as a decimal (1.48 = 148%), straight from Robinhood get_option_quotes.
"""

from __future__ import annotations

import json
import math
import sys
from datetime import date, timedelta

# Thresholds, mirrored in SKILL.md. Change both together.
BIG_MOVE_PCT = 8.0
BIG_VOLUME_X = 3.0
WITH_SECTOR_PTS = 3.0
MAX_SPREAD_OF_MID = 0.35
MIN_OI = 25
ATM_PUT_CALL_IV_GAP = 0.20
TARGET_DELTA = 0.25
DELTA_TOLERANCE = 0.10
RICH_IVP52, RICH_IVP26, RICH_IV_HV = 0.60, 0.50, 1.3
RICH_PUT_RATIO, RICH_PUT_JUMP = 1.15, 0.10
NOT_PAID_PUT_RATIO = 1.00
SHAPE_GAP = 0.05
INVERTED_TERM = 1.20
CRUSH_TRADING_DAYS = 5
CHEAP_IVP52 = 0.25


def _d(s: str) -> date:
    return date.fromisoformat(s)


# --------------------------------------------------------------------- price

def price(d: dict) -> dict:
    """Day move, volume vs 30-day average, HV30, excess move vs XBI.

    bars: daily [{close, volume}] oldest first, at least 2 (31+ for HV30 and
    the volume average). The last bar is the session being reported.
    xbi_change_pct: XBI's % change for the same session.
    """
    bars = d["bars"]
    if len(bars) < 2:
        raise ValueError("need at least two daily bars")
    closes = [float(b["close"]) for b in bars]
    last, prev = closes[-1], closes[-2]
    chg = (last / prev - 1) * 100
    out = {"close": last, "prev_close": prev, "change_pct": round(chg, 2)}
    hist = [float(b["volume"]) for b in bars[-31:-1]]
    if hist:
        avg = sum(hist) / len(hist)
        out["avg_volume"] = round(avg)
        out["volume_x_avg"] = round(float(bars[-1]["volume"]) / avg, 2) if avg else None
    if len(closes) >= 31:
        rets = [math.log(closes[i] / closes[i - 1]) for i in range(len(closes) - 30, len(closes))]
        mean = sum(rets) / len(rets)
        var = sum((r - mean) ** 2 for r in rets) / (len(rets) - 1)
        out["hv30_from_bars"] = round(math.sqrt(var) * math.sqrt(252), 4)
    if d.get("xbi_change_pct") is not None:
        excess = chg - float(d["xbi_change_pct"])
        out["excess_vs_xbi_pts"] = round(excess, 2)
        out["moved_with_biotech"] = abs(excess) < WITH_SECTOR_PTS
    out["big_move"] = abs(chg) >= BIG_MOVE_PCT or (out.get("volume_x_avg") or 0) >= BIG_VOLUME_X
    return out


# ------------------------------------------------------------------- overlay

def overlay(d: dict) -> dict:
    """Where a catalyst falls against each expiry.

    as_of, expiries, and event_date or window_start + window_end; optional
    holidays. A weekend/holiday decision date can land on the prior trading
    day, so the expiry on that day counts as carrying it. Statuses: before,
    carries, in_window (open-ended guidance overlaps; treat as carrying).
    Also returns trading days from as_of to the event (or window start).
    """
    as_of = _d(d["as_of"])
    holidays = {_d(h) for h in d.get("holidays", [])}
    expiries = sorted(_d(e) for e in d["expiries"])
    out: dict = {"expiries": []}
    if d.get("event_date"):
        ev = _d(d["event_date"])
        eff = ev
        while eff.weekday() >= 5 or eff in holidays:
            eff -= timedelta(days=1)
        if eff != ev:
            out["note"] = f"{ev} is not a trading day; a decision can land on {eff} or earlier"
        start = end = eff
        out["dated"] = True
    else:
        out["dated"] = False
        start, end = _d(d["window_start"]), _d(d["window_end"])
    for e in expiries:
        status = "before" if e < start else "carries" if e >= end else "in_window"
        out["expiries"].append({"expiry": e.isoformat(), "dte": (e - as_of).days, "status": status})
    days, cur = 0, as_of
    while cur < start:
        cur += timedelta(days=1)
        if cur.weekday() < 5 and cur not in holidays:
            days += 1
    out["trading_days_to_event"] = days
    return out


# ---------------------------------------------------------------------- skew

def usable(c: dict) -> bool:
    bid, ask = float(c.get("bid") or 0), float(c.get("ask") or 0)
    if bid <= 0 or ask <= 0 or c.get("iv") in (None, 0):
        return False
    mid = (bid + ask) / 2
    if (ask - bid) / mid > MAX_SPREAD_OF_MID:
        return False
    return float(c.get("oi") or 0) >= MIN_OI or float(c.get("volume") or 0) > 0


def _atm_iv(spot: float, contracts: list[dict]) -> tuple[float | None, float | None]:
    strikes = sorted({float(c["strike"]) for c in contracts}, key=lambda k: abs(k - spot))
    for k in strikes[:3]:
        put = next((c for c in contracts if c["type"] == "put" and float(c["strike"]) == k and usable(c)), None)
        call = next((c for c in contracts if c["type"] == "call" and float(c["strike"]) == k and usable(c)), None)
        if put and call and abs(float(put["iv"]) - float(call["iv"])) <= ATM_PUT_CALL_IV_GAP:
            return round((float(put["iv"]) + float(call["iv"])) / 2, 4), k
    return None, None


def _wing(contracts: list[dict], kind: str) -> dict | None:
    cands = [c for c in contracts if c["type"] == kind and usable(c) and c.get("delta") is not None
             and abs(abs(float(c["delta"])) - TARGET_DELTA) <= DELTA_TOLERANCE]
    return min(cands, key=lambda c: abs(abs(float(c["delta"])) - TARGET_DELTA)) if cands else None


def skew(d: dict) -> dict:
    """ATM IV per expiry, 25-delta put/call ratios (back month), term ratio.

    spot, front: contracts of the front expiry, back: contracts of the
    ~75-day expiry. Unusable quotes (no bid/ask, spread > 35% of mid, OI < 25
    with no volume) are ignored; missing readings come back as None.
    """
    spot = float(d["spot"])
    out: dict = {}
    front_atm, fk = _atm_iv(spot, d.get("front", []))
    back_atm, bk = _atm_iv(spot, d.get("back", []))
    out["front_atm_iv"], out["back_atm_iv"] = front_atm, back_atm
    out["atm_strikes"] = {"front": fk, "back": bk}
    put = _wing(d.get("back", []), "put")
    call = _wing(d.get("back", []), "call")
    out["put_25d"] = {"strike": float(put["strike"]), "iv": float(put["iv"]), "delta": float(put["delta"])} if put else None
    out["call_25d"] = {"strike": float(call["strike"]), "iv": float(call["iv"]), "delta": float(call["delta"])} if call else None
    out["put_ratio"] = round(float(put["iv"]) / back_atm, 3) if put and back_atm else None
    out["call_ratio"] = round(float(call["iv"]) / back_atm, 3) if call and back_atm else None
    if out["put_ratio"] and out["call_ratio"]:
        gap = out["put_ratio"] - out["call_ratio"]
        out["shape"] = "put skew" if gap >= SHAPE_GAP else "call skew" if gap <= -SHAPE_GAP else "flat"
    else:
        out["shape"] = None
    out["term_ratio"] = round(front_atm / back_atm, 3) if front_atm and back_atm else None
    missing = [k for k in ("front_atm_iv", "back_atm_iv", "put_ratio", "call_ratio") if out[k] is None]
    if missing:
        out["n/a"] = f"chain too thin for: {', '.join(missing)}"
    return out


# ------------------------------------------------------------------ contract

def contract(d: dict) -> dict:
    """The put to look at: usable, 25-35% OTM, most open interest.

    spot, dte, puts (contracts of one expiry). Optional otm_min/otm_max.
    ROC = mid / (strike - mid) on cash-secured capital; annualized x 365/dte.
    """
    spot, dte = float(d["spot"]), int(d["dte"])
    lo, hi = float(d.get("otm_min", 0.25)), float(d.get("otm_max", 0.35))
    cands = []
    for c in d["puts"]:
        k = float(c["strike"])
        otm = (spot - k) / spot
        if lo <= otm <= hi and usable(c):
            cands.append((float(c.get("oi") or 0), otm, c))
    if not cands:
        return {"contract": None, "note": f"no usable put {lo:.0%}-{hi:.0%} OTM (chain too thin)"}
    _, otm, c = max(cands, key=lambda x: (x[0], -abs(x[1] - (lo + hi) / 2)))
    k = float(c["strike"])
    bid, ask = float(c["bid"]), float(c["ask"])
    mid = (bid + ask) / 2
    roc = mid / (k - mid)
    return {"contract": {
        "strike": k, "bid": bid, "ask": ask, "mid": round(mid, 3), "otm_pct": round(otm * 100, 1),
        "oi": c.get("oi"), "iv": c.get("iv"), "delta": c.get("delta"), "dte": dte,
        "breakeven": round(k - mid, 3), "roc_pct": round(roc * 100, 1),
        "annualized_pct": round(roc * 365 / dte * 100, 1),
    }}


# -------------------------------------------------------------------- assess

def assess(d: dict) -> dict:
    """Setup flags from the measured numbers. Missing inputs skip their flag.

    ivp52, ivp26 (IBKR, fractions), iv30, hv30 (fractions), put_ratio,
    call_ratio, shape, put_ratio_baseline, term_ratio, front_status and
    back_status (from overlay: before / carries / in_window, or None when
    there is no catalyst), trading_days_to_event, event_dated (False for an
    open-ended window like "Q4", which never triggers IV CRUSH WATCH).
    """
    g = d.get
    flags, why = [], {}
    carries = ("carries", "in_window")
    if g("ivp52") is not None and g("ivp26") is not None and g("iv30") and g("hv30"):
        ratio = float(g("iv30")) / float(g("hv30"))
        why["iv_hv"] = round(ratio, 2)
        if float(g("ivp52")) >= RICH_IVP52 and float(g("ivp26")) >= RICH_IVP26 and ratio >= RICH_IV_HV:
            flags.append("RICH PREMIUM")
    if g("ivp52") is not None and float(g("ivp52")) < CHEAP_IVP52:
        flags.append("CHEAP")
    pr = g("put_ratio")
    if pr is not None:
        jump = pr - float(g("put_ratio_baseline")) if g("put_ratio_baseline") is not None else 0
        if pr >= RICH_PUT_RATIO or jump >= RICH_PUT_JUMP:
            flags.append("RICH PUTS")
        if pr <= NOT_PAID_PUT_RATIO or g("shape") == "call skew":
            flags.append("PUTS NOT PAID")
    fs, bs, tr = g("front_status"), g("back_status"), g("term_ratio")
    if fs in carries and tr is not None and tr >= INVERTED_TERM:
        flags.append("EVENT IN FRONT")
    elif fs == "before" and bs in carries:
        flags.append("EVENT IN BACK")
    elif tr is not None and tr >= INVERTED_TERM and bs not in carries:
        flags.append("UNEXPLAINED INVERSION")
    if (g("trading_days_to_event") is not None and fs is not None and g("event_dated", True)
            and int(g("trading_days_to_event")) <= CRUSH_TRADING_DAYS):
        flags.append("IV CRUSH WATCH")
    sell_side = [f for f in flags if f in ("RICH PREMIUM", "RICH PUTS", "EVENT IN FRONT", "EVENT IN BACK")]
    return {"flags": flags, "needs_contract": bool(sell_side), "inputs": why}


COMMANDS = {"price": price, "overlay": overlay, "skew": skew, "contract": contract, "assess": assess}


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[1] not in COMMANDS:
        print(f"usage: sentinel_calc.py {{{'|'.join(COMMANDS)}}} '<json>'", file=sys.stderr)
        return 2
    raw = argv[2] if len(argv) > 2 else sys.stdin.read()
    print(json.dumps(COMMANDS[argv[1]](json.loads(raw)), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
