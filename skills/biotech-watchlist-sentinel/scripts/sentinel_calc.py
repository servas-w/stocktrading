"""Deterministic math for the Biotech Watchlist Sentinel (Claude version).

Stdlib only, no network. Import and call, or run as a CLI with one JSON
object as the argument (or on stdin):

    python3 sentinel_calc.py moves    '{"quotes": [...]}'
    python3 sentinel_calc.py price    '{"as_of": "2026-10-29", "bars": [...], "xbi_bars": [...]}'
    python3 sentinel_calc.py overlay  '{"as_of": "2026-10-29", "event_date": "2026-11-22", "expiries": [...]}'
    python3 sentinel_calc.py skew     '{"spot": 6.1, "front": [...], "back": [...]}'
    python3 sentinel_calc.py contract '{"spot": 6.1, "dte": 79, "puts": [...]}'
    python3 sentinel_calc.py assess   '{"ivp52": 0.71, ...}'

Robinhood returns numbers as strings and leaves fields blank on dead
contracts; every input goes through _num, so "1.25", 1.25, "" and None are
all fine. Contracts: {type: put|call, strike, bid, ask, iv, delta, oi,
volume}, iv as a decimal (1.48 = 148%). Bars: {begins_at or date, close or
close_price, volume, interpolated}.
"""

from __future__ import annotations

import json
import math
import sys
from datetime import date, timedelta

# Thresholds, mirrored in SKILL.md. Change both together.
BIG_MOVE_PCT = 8.0
NEWS_CHECK_MOVE_PCT = 5.0
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

# NYSE full-day closures. Re-check each January.
HOLIDAYS = {
    "2026-11-26", "2026-12-25",
    "2027-01-01", "2027-01-18", "2027-02-15", "2027-03-26", "2027-05-31",
    "2027-06-18", "2027-07-05", "2027-09-06", "2027-11-25", "2027-12-24",
}


def _d(s: str) -> date:
    return date.fromisoformat(str(s)[:10])


def _num(v) -> float | None:
    """Robinhood-proof float: strings, blanks, None and NaN all handled."""
    if v is None:
        return None
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(x) else x


def _holidays(d: dict) -> set[date]:
    return {_d(h) for h in d.get("holidays", HOLIDAYS)}


def is_trading_day(day: date, holidays: set[date]) -> bool:
    return day.weekday() < 5 and day not in holidays


def last_session(as_of: date, holidays: set[date], after_close: bool = True) -> date:
    """Most recent completed US session as of `as_of` (an ET date)."""
    day = as_of if after_close else as_of - timedelta(days=1)
    while not is_trading_day(day, holidays):
        day -= timedelta(days=1)
    return day


# --------------------------------------------------------------------- moves

def moves(d: dict) -> dict:
    """Hourly-watch price check from one batched get_equity_quotes call.

    quotes: Robinhood quote objects as returned ({symbol, last_trade_price,
    venue_last_trade_time, last_non_reg_trade_price,
    venue_last_non_reg_trade_time, adjusted_previous_close}), or a plain
    {symbol, last, previous_close}. Uses whichever print is more recent, so
    pre-market and after-hours moves are caught. Flags alert (>= 8%) and
    news_check (>= 5%).
    """
    rows = []
    for q in d["quotes"]:
        q = q.get("quote", q)
        last, session = _num(q.get("last")), "given"
        if last is None:
            reg, ext = _num(q.get("last_trade_price")), _num(q.get("last_non_reg_trade_price"))
            reg_t, ext_t = q.get("venue_last_trade_time") or "", q.get("venue_last_non_reg_trade_time") or ""
            if ext and (not reg or ext_t > reg_t):
                last, session = ext, "extended hours"
            else:
                last, session = reg, "regular"
        prev = _num(q.get("adjusted_previous_close")) or _num(q.get("previous_close"))
        if not last or not prev:
            rows.append({"symbol": q.get("symbol"), "change_pct": None, "note": "quote missing"})
            continue
        chg = (last / prev - 1) * 100
        rows.append({"symbol": q.get("symbol"), "last": last, "prev_close": prev, "session": session,
                     "change_pct": round(chg, 2), "alert": abs(chg) >= BIG_MOVE_PCT,
                     "news_check": abs(chg) >= NEWS_CHECK_MOVE_PCT})
    return {"moves": rows}


# --------------------------------------------------------------------- price

def _clean_bars(bars: list[dict]) -> list[dict]:
    out = []
    for b in bars:
        if b.get("interpolated") in (True, "true", "True"):
            continue  # Robinhood gap filler: no new information
        close = _num(b.get("close", b.get("close_price")))
        if close:
            out.append({"date": b.get("date") or b.get("begins_at"), "close": close,
                        "volume": _num(b.get("volume")) or 0.0})
    return out


def _change(bars: list[dict]) -> float:
    return (bars[-1]["close"] / bars[-2]["close"] - 1) * 100


def price(d: dict) -> dict:
    """Day move, volume vs 30-day average, HV30, excess move vs XBI, staleness.

    bars: daily bars oldest first (31+ real bars for HV30 and the volume
    average); interpolated filler bars are dropped. xbi_bars: XBI daily bars
    for the same range (or xbi_change_pct). as_of (ET date) and after_close
    (default true) check that the last bar is the latest completed session.
    """
    bars = _clean_bars(d["bars"])
    if len(bars) < 2:
        raise ValueError("need at least two real daily bars")
    chg = _change(bars)
    out: dict = {"close": bars[-1]["close"], "prev_close": bars[-2]["close"],
                 "change_pct": round(chg, 2), "session": bars[-1]["date"]}
    if d.get("as_of") and bars[-1]["date"]:
        expected = last_session(_d(d["as_of"]), _holidays(d), d.get("after_close", True))
        out["expected_session"] = expected.isoformat()
        out["market_closed_or_stale"] = _d(bars[-1]["date"]) != expected
    hist = [b["volume"] for b in bars[-31:-1]]
    if hist:
        avg = sum(hist) / len(hist)
        out["avg_volume"] = round(avg)
        out["volume_x_avg"] = round(bars[-1]["volume"] / avg, 2) if avg else None
    if len(bars) >= 31:
        closes = [b["close"] for b in bars[-31:]]
        rets = [math.log(closes[i] / closes[i - 1]) for i in range(1, len(closes))]
        mean = sum(rets) / len(rets)
        var = sum((r - mean) ** 2 for r in rets) / (len(rets) - 1)
        out["hv30_from_bars"] = round(math.sqrt(var) * math.sqrt(252), 4)
    xbi = None
    if d.get("xbi_bars"):
        xb = _clean_bars(d["xbi_bars"])
        if len(xb) >= 2:
            if xb[-1]["date"] and bars[-1]["date"] and str(xb[-1]["date"])[:10] != str(bars[-1]["date"])[:10]:
                out["xbi_note"] = "XBI bars end on a different session"
            xbi = _change(xb)
    elif d.get("xbi_change_pct") is not None:
        xbi = _num(d["xbi_change_pct"])
    if xbi is not None:
        out["xbi_change_pct"] = round(xbi, 2)
        out["excess_vs_xbi_pts"] = round(chg - xbi, 2)
        out["moved_with_biotech"] = abs(chg - xbi) < WITH_SECTOR_PTS
    out["big_move"] = abs(chg) >= BIG_MOVE_PCT or (out.get("volume_x_avg") or 0) >= BIG_VOLUME_X
    return out


# ------------------------------------------------------------------- overlay

def overlay(d: dict) -> dict:
    """Where a catalyst falls against each expiry.

    as_of, expiries, and event_date or window_start + window_end; optional
    holidays (defaults to HOLIDAYS). A weekend/holiday decision date can land
    on the prior trading day, so that day's expiry counts as carrying it.
    Statuses: before, carries, in_window (open-ended guidance overlaps; treat
    as carrying), past (the event date is behind as_of: the cached catalyst
    is stale and must be refreshed).
    """
    as_of = _d(d["as_of"])
    holidays = _holidays(d)
    expiries = sorted(_d(e) for e in d["expiries"])
    out: dict = {"expiries": []}
    if d.get("event_date"):
        ev = _d(d["event_date"])
        eff = ev
        while not is_trading_day(eff, holidays):
            eff -= timedelta(days=1)
        if eff != ev:
            out["note"] = f"{ev} is not a trading day; a decision can land on {eff} or earlier"
        start = end = eff
        out["dated"] = True
        passed = ev < as_of
    else:
        start, end = _d(d["window_start"]), _d(d["window_end"])
        out["dated"] = False
        passed = end < as_of
    out["event_passed"] = passed
    if passed:
        out["warning"] = "catalyst date has passed: refresh the catalyst before reading IV against it"
    for e in expiries:
        status = ("past" if passed else "before" if e < start
                  else "carries" if e >= end else "in_window")
        out["expiries"].append({"expiry": e.isoformat(), "dte": (e - as_of).days, "status": status})
    days, cur = 0, as_of
    while cur < start:
        cur += timedelta(days=1)
        if is_trading_day(cur, holidays):
            days += 1
    out["trading_days_to_event"] = None if passed else days
    return out


# ---------------------------------------------------------------------- skew

def _c(c: dict) -> dict:
    return {"type": str(c.get("type", "")).lower(), "strike": _num(c.get("strike")),
            "bid": _num(c.get("bid")), "ask": _num(c.get("ask")), "iv": _num(c.get("iv")),
            "delta": _num(c.get("delta")), "oi": _num(c.get("oi")) or 0.0,
            "volume": _num(c.get("volume")) or 0.0}


def usable(c: dict) -> bool:
    c = _c(c)
    if not c["bid"] or not c["ask"] or c["bid"] <= 0 or c["ask"] <= 0 or not c["iv"] or c["strike"] is None:
        return False
    mid = (c["bid"] + c["ask"]) / 2
    if (c["ask"] - c["bid"]) / mid > MAX_SPREAD_OF_MID:
        return False
    return c["oi"] >= MIN_OI or c["volume"] > 0


def _usable_list(contracts: list[dict]) -> list[dict]:
    return [_c(c) for c in contracts if usable(c)]


def _atm_iv(spot: float, contracts: list[dict]) -> tuple[float | None, float | None]:
    good = _usable_list(contracts)
    for k in sorted({c["strike"] for c in good}, key=lambda k: abs(k - spot))[:3]:
        put = next((c for c in good if c["type"] == "put" and c["strike"] == k), None)
        call = next((c for c in good if c["type"] == "call" and c["strike"] == k), None)
        if put and call and abs(put["iv"] - call["iv"]) <= ATM_PUT_CALL_IV_GAP:
            return round((put["iv"] + call["iv"]) / 2, 4), k
    return None, None


def _wing(contracts: list[dict], kind: str) -> dict | None:
    cands = [c for c in _usable_list(contracts) if c["type"] == kind and c["delta"] is not None
             and abs(abs(c["delta"]) - TARGET_DELTA) <= DELTA_TOLERANCE]
    return min(cands, key=lambda c: abs(abs(c["delta"]) - TARGET_DELTA)) if cands else None


def skew(d: dict) -> dict:
    """ATM IV per expiry, 25-delta put/call ratios (back month), term ratio.

    spot, front: contracts of the front expiry, back: contracts of the
    ~75-day expiry. Unusable quotes (no bid/ask/IV, spread > 35% of mid, OI <
    25 with no volume) are ignored; missing readings come back as None.
    """
    spot = float(d["spot"])
    out: dict = {}
    front_atm, fk = _atm_iv(spot, d.get("front", []))
    back_atm, bk = _atm_iv(spot, d.get("back", []))
    out["front_atm_iv"], out["back_atm_iv"] = front_atm, back_atm
    out["atm_strikes"] = {"front": fk, "back": bk}
    put, call = _wing(d.get("back", []), "put"), _wing(d.get("back", []), "call")
    out["put_25d"] = {k: put[k] for k in ("strike", "iv", "delta")} if put else None
    out["call_25d"] = {k: call[k] for k in ("strike", "iv", "delta")} if call else None
    out["put_ratio"] = round(put["iv"] / back_atm, 3) if put and back_atm else None
    out["call_ratio"] = round(call["iv"] / back_atm, 3) if call and back_atm else None
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
    Small biotechs often list $1 or $0.50 strikes only, so when nothing sits
    in the band, the usable put closest to the band's middle within 15-50%
    OTM is used instead and flagged `outside_target_band`.
    ROC = credit / (strike - credit) on cash-secured capital, shown at the
    mid and at the bid (thin biotech chains often fill near the bid).
    """
    spot, dte = float(d["spot"]), int(d["dte"])
    lo, hi = float(d.get("otm_min", 0.25)), float(d.get("otm_max", 0.35))
    cands = []
    for c in _usable_list(d["puts"]):
        otm = (spot - c["strike"]) / spot
        if c["type"] in ("put", "") and lo <= otm <= hi:
            cands.append((c["oi"], otm, c))
    fallback = False
    if not cands:
        mid_band = (lo + hi) / 2
        wide = [(c["oi"], (spot - c["strike"]) / spot, c) for c in _usable_list(d["puts"])
                if c["type"] in ("put", "") and 0.15 <= (spot - c["strike"]) / spot <= 0.50]
        if not wide:
            return {"contract": None, "note": "no usable put 15%-50% OTM (chain too thin, or quotes stale outside market hours)"}
        cands, fallback = [min(wide, key=lambda x: abs(x[1] - mid_band))], True
    _, otm, c = max(cands, key=lambda x: (x[0], -abs(x[1] - (lo + hi) / 2)))
    k, bid, ask = c["strike"], c["bid"], c["ask"]
    mid = (bid + ask) / 2
    roc_mid, roc_bid = mid / (k - mid), bid / (k - bid)
    return {"contract": {
        "strike": k, "bid": bid, "ask": ask, "mid": round(mid, 3), "otm_pct": round(otm * 100, 1),
        "oi": c["oi"], "iv": c["iv"], "delta": c["delta"], "dte": dte,
        "breakeven_mid": round(k - mid, 3),
        "roc_mid_pct": round(roc_mid * 100, 1), "annualized_mid_pct": round(roc_mid * 365 / dte * 100, 1),
        "roc_bid_pct": round(roc_bid * 100, 1), "annualized_bid_pct": round(roc_bid * 365 / dte * 100, 1),
        "outside_target_band": fallback,
    }}


# -------------------------------------------------------------------- assess

def assess(d: dict) -> dict:
    """Setup flags from the measured numbers. Missing inputs skip their flag.

    ivp52, ivp26 (IBKR, fractions), iv30, hv30 (fractions), put_ratio,
    call_ratio, shape, put_ratio_baseline, term_ratio, front_status and
    back_status (from overlay; None when there is no catalyst),
    trading_days_to_event, event_dated (False for an open-ended window like
    "Q4", which never triggers IV CRUSH WATCH).
    """
    g = lambda k: _num(d.get(k))  # noqa: E731
    flags, inputs = [], {}
    carries = ("carries", "in_window")
    ivp52, ivp26, iv30, hv30 = g("ivp52"), g("ivp26"), g("iv30"), g("hv30")
    if None not in (ivp52, ivp26) and iv30 and hv30:
        inputs["iv_hv"] = round(iv30 / hv30, 2)
        if ivp52 >= RICH_IVP52 and ivp26 >= RICH_IVP26 and iv30 / hv30 >= RICH_IV_HV:
            flags.append("RICH PREMIUM")
    if ivp52 is not None and ivp52 < CHEAP_IVP52:
        flags.append("CHEAP")
    pr, base = g("put_ratio"), g("put_ratio_baseline")
    if pr is not None:
        rich = pr >= RICH_PUT_RATIO or (base is not None and pr - base >= RICH_PUT_JUMP)
        if rich:
            flags.append("RICH PUTS")
        elif pr <= NOT_PAID_PUT_RATIO or d.get("shape") == "call skew":
            flags.append("PUTS NOT PAID")
    fs, bs, tr = d.get("front_status"), d.get("back_status"), g("term_ratio")
    if fs == "past" or bs == "past":
        flags.append("STALE CATALYST")
    elif fs in carries and tr is not None and tr >= INVERTED_TERM:
        flags.append("EVENT IN FRONT")
    elif fs == "before" and bs in carries:
        flags.append("EVENT IN BACK")
    elif tr is not None and tr >= INVERTED_TERM and bs not in carries:
        flags.append("UNEXPLAINED INVERSION")
    tde = g("trading_days_to_event")
    if (tde is not None and fs not in (None, "past") and d.get("event_dated", True)
            and tde <= CRUSH_TRADING_DAYS):
        flags.append("IV CRUSH WATCH")
    sell_side = [f for f in flags if f in ("RICH PREMIUM", "RICH PUTS", "EVENT IN FRONT", "EVENT IN BACK")]
    return {"flags": flags, "needs_contract": bool(sell_side), "inputs": inputs}


COMMANDS = {"moves": moves, "price": price, "overlay": overlay, "skew": skew,
            "contract": contract, "assess": assess}


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[1] not in COMMANDS:
        print(f"usage: sentinel_calc.py {{{'|'.join(COMMANDS)}}} '<json>'", file=sys.stderr)
        return 2
    raw = argv[2] if len(argv) > 2 else sys.stdin.read()
    print(json.dumps(COMMANDS[argv[1]](json.loads(raw)), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
