"""Deterministic math for the Biotech Ticker Sentinel.

Stdlib only, no network. Import it and call the functions, or run it as a
CLI with one JSON object as the argument (or on stdin):

    import sentinel_calc as c
    c.iv30({"points": [{"dte": 23, "iv": 1.9}, {"dte": 51, "iv": 1.6}]})

    python3 sentinel_calc.py overlay '{"as_of": "2026-10-28", ...}'

Commands: iv30, overlay, event_move, position, floor.
IVs are decimals (1.90 = 190%). Dates are ISO (YYYY-MM-DD). Money is $M in
`floor`, per-share / per-contract dollars elsewhere.
"""

from __future__ import annotations

import json
import math
import sys
from datetime import date, timedelta

DAYS_PER_YEAR = 365.0
# Expected |x| of a normal variable is sqrt(2/pi) ~ 0.798 of its std dev.
ABS_MOVE_FACTOR = math.sqrt(2.0 / math.pi)

# Tunable defaults, mirrored in SKILL.md "Thresholds".
DEFENSE_CUSHION = 0.07
DEFENSE_DELTA = 0.30
NEAR_MONEY = 0.20
DEAD_MARK = 0.05
TAKE_PROFIT = 50.0


def _d(s: str) -> date:
    return date.fromisoformat(s)


def _days(a: str, b: str) -> int:
    return (_d(b) - _d(a)).days


# ---------------------------------------------------------------------- iv30

def iv30(d: dict) -> dict:
    """Constant-maturity 30-day IV, so day-over-day changes compare like with like.

    points: [{dte, iv}] for at least two expiries (ATM IV of each). Interpolates
    total variance (iv^2 * t) linearly in time, the standard way to blend IVs.
    target_dte overrides 30.
    """
    target = float(d.get("target_dte", 30))
    pts = sorted((float(p["dte"]), float(p["iv"])) for p in d["points"])
    if len(pts) < 2:
        raise ValueError("need ATM IV for at least two expiries")
    out: dict = {}
    below = [p for p in pts if p[0] <= target]
    above = [p for p in pts if p[0] >= target]
    if not below or not above:
        dte, iv = pts[0] if not below else pts[-1]
        out["iv30"] = round(iv, 4)
        out["note"] = f"no expiry on both sides of {target:g}d: used the {dte:g}d IV flat"
    else:
        (t1, s1), (t2, s2) = below[-1], above[0]
        if t1 == t2:
            out["iv30"] = round(s1, 4)
        else:
            w1, w2 = s1 * s1 * t1, s2 * s2 * t2
            w = w1 + (w2 - w1) * (target - t1) / (t2 - t1)
            out["iv30"] = round(math.sqrt(max(w, 0.0) / target), 4)
            out["bracket_dte"] = [t1, t2]
    if d.get("baseline_iv30") is not None:
        out["change_pts"] = round((out["iv30"] - float(d["baseline_iv30"])) * 100, 1)
    return out


# ------------------------------------------------------------------- overlay

def overlay(d: dict) -> dict:
    """Classify expiries against a dated event or an open-ended window.

    Required: as_of, expiries (list), and either event_date or window_start +
    window_end. Optional: holidays (list of dates the market is shut).
    Statuses: before (scheduled date is after expiry; an early action can
    still land), ambiguous (event falls on a weekend/holiday right after this
    expiry; it may land before or after the close), carries (expiry is on or
    after the event), in_window (open-ended guidance overlaps this expiry).
    """
    as_of = _d(d["as_of"])
    expiries = sorted(_d(e) for e in d["expiries"])
    out: dict = {"expiries": []}
    if d.get("event_date"):
        ev = _d(d["event_date"])
        holidays = {_d(h) for h in d.get("holidays", [])}
        earliest = ev
        while earliest.weekday() >= 5 or earliest in holidays:
            earliest -= timedelta(days=1)
        if earliest != ev:
            out["note"] = (f"{ev} is not a trading day; action may come on or before "
                           f"{earliest} (FDA can also act early or miss the date)")
        status_of = lambda e: "before" if e < earliest else "ambiguous" if e < ev else "carries"  # noqa: E731
        pre = [e for e in expiries if e < earliest]
        post = [e for e in expiries if e >= ev]
    else:
        ws, we = _d(d["window_start"]), _d(d["window_end"])
        status_of = lambda e: "before" if e < ws else "carries" if e >= we else "in_window"  # noqa: E731
        pre = [e for e in expiries if e < ws]
        post = [e for e in expiries if e >= we]
    for e in expiries:
        out["expiries"].append({"expiry": e.isoformat(), "dte": (e - as_of).days, "status": status_of(e)})
    out["pre_event_expiry"] = pre[-1].isoformat() if pre else None
    out["post_event_expiry"] = post[0].isoformat() if post else None
    return out


# ---------------------------------------------------------------- event_move

def event_move(d: dict) -> dict:
    """Market-implied move for a binary event, plus a failure-case check.

    Preferred: pre_iv (ATM IV of the last expiry before the event), post_iv
    and post_dte (or post_expiry + as_of) for the first expiry after it. The
    pre-event IV stands in for base vol; the variance left over is the event.
    Moves are in log space, so the down level never goes below zero.
    Fallback: straddle (ATM call + put mid, first post-event expiry). It also
    holds base vol to expiry, so it overstates the event alone.

    Optional short-put check: strike, credit, qty, long_strike (spread).
    Binary events are two outcomes, not a bell curve, so the "average move"
    test is not enough. Pass fail_level (where the stock trades if the event
    fails: usually cash per share, or a CRL/failed-readout analog) to get the
    loss if it fails.
    """
    spot = float(d["spot"])
    out: dict = {}
    down = None
    if d.get("pre_iv") and d.get("post_iv"):
        t2 = (float(d["post_dte"]) if d.get("post_dte") is not None
              else _days(d["as_of"], d["post_expiry"])) / DAYS_PER_YEAR
        s1, s2 = float(d["pre_iv"]), float(d["post_iv"])
        event_var = (s2 * s2 - s1 * s1) * t2
        out["term_structure_inverted"] = s2 > s1
        if event_var <= 0:
            out["event_std_move_pct"] = 0.0
            out["note"] = "post-event IV not above pre-event IV: no event premium priced"
        else:
            std = math.sqrt(event_var)
            m = std * ABS_MOVE_FACTOR
            out["event_std_move_pct"] = round(std * 100, 1)
            out["expected_abs_move_pct"] = round(m * 100, 1)
            down = spot * math.exp(-m)
            out["expected_down_level"] = round(down, 3)
            out["expected_up_level"] = round(spot * math.exp(m), 3)
    if d.get("straddle"):
        pct = float(d["straddle"]) / spot
        out["straddle_move_pct"] = round(pct * 100, 1)
        out["straddle_low"] = round(max(spot * (1 - pct), 0.0), 3)
        out["straddle_high"] = round(spot * (1 + pct), 3)
        if down is None:
            down = out["straddle_low"]
            out["down_level_source"] = "straddle (overstates the event alone)"
    if not out:
        raise ValueError("need pre_iv + post_iv + post_dte/post_expiry, or straddle")

    if d.get("strike") is not None:
        k = float(d["strike"])
        credit = float(d.get("credit", 0))
        be = k - credit
        out["breakeven"] = round(be, 3)
        if down is not None:
            out["move_test"] = ("strike outside expected move" if k <= down
                                else "strike inside move, breakeven outside" if be <= down
                                else "breakeven inside expected move")
        if d.get("fail_level") is not None:
            fail = float(d["fail_level"])
            qty = int(d.get("qty", 1))
            width = k - float(d["long_strike"]) if d.get("long_strike") is not None else k
            loss_ps = min(max(be - fail, 0.0), width - credit)
            out["if_event_fails"] = {
                "stock_at": round(fail, 3),
                "short_put": "OTM" if fail >= k else "ITM",
                "loss": round(loss_ps * 100 * qty, 2),
            }
    return out


# ------------------------------------------------------------------ position

def _leg(spot: float, lg: dict, as_of: str | None) -> dict:
    kind = lg.get("type", "short_put")
    k, qty = float(lg["strike"]), int(lg["qty"])
    dte = int(lg["dte"]) if lg.get("dte") is not None else _days(as_of, lg["expiry"])
    row = {"type": kind, "strike": k, "qty": qty, "dte": dte}
    if lg.get("expiry"):
        row["expiry"] = lg["expiry"]
    mark = float(lg["mark"]) if lg.get("mark") is not None else None
    delta = abs(float(lg["delta"])) if lg.get("delta") is not None else None  # sign-proof
    flags = []

    if kind == "long_put":
        cost = float(lg["cost"])
        row["cost"] = cost
        if mark is not None:
            row["pnl"] = round((mark - cost) * 100 * qty, 2)
            row["pnl_pct"] = round((mark - cost) / cost * 100, 1) if cost else None
            if mark >= 2 * cost:
                flags.append("hedge worth >= 2x cost: consider monetizing")
        if delta is not None:
            row["delta"] = delta
        row["flags"] = flags
        return row

    credit = float(lg["credit"])
    long_k = lg.get("long_strike")
    width = k - float(long_k) if long_k is not None else k
    if long_k is not None:
        row["long_strike"] = float(long_k)
    cushion = (spot - k) / spot
    intrinsic = min(max(0.0, k - spot), width)
    row.update({
        "credit": credit,
        "breakeven": round(k - credit, 3),
        "cushion_to_strike_pct": round(cushion * 100, 1),
        "cushion_to_breakeven_pct": round((spot - (k - credit)) / spot * 100, 1),
        "max_loss": round((width - credit) * 100 * qty, 2),
    })
    if spot < k:
        flags.append("ITM")
    elif cushion <= DEFENSE_CUSHION:
        flags.append("within 7% of strike")
    if delta is not None and delta >= DEFENSE_DELTA:
        flags.append("delta >= 0.30")
    if dte <= 21 and cushion <= NEAR_MONEY:
        flags.append("<= 21 DTE near the money")
    if mark is not None:
        row["captured_pct"] = round((credit - mark) / credit * 100, 1)
        if mark <= DEAD_MARK:
            flags.append("mark <= $0.05: buy back")
        elif row["captured_pct"] >= TAKE_PROFIT:
            flags.append(">= 50% captured")
        if intrinsic > 0 and mark < intrinsic - 0.005:
            flags.append("mark below intrinsic: quote stale")
    row["flags"] = flags
    return row


def position(d: dict) -> dict:
    """Your position on ONE monitored name: how the news touches it.

    Input: spot, as_of, held_shares (negative = short), avg_cost (shares),
    legs: [{type: short_put | long_put, strike, long_strike (spread), qty,
    expiry or dte, credit (short) or cost (long), mark, delta}].
    """
    spot = float(d["spot"])
    legs = [_leg(spot, lg, d.get("as_of")) for lg in d.get("legs", [])]
    out: dict = {"legs": legs}
    sh = float(d.get("held_shares", 0))
    if sh:
        stock = {"shares": sh, "value": round(sh * spot, 2)}
        if d.get("avg_cost") is not None:
            cost = float(d["avg_cost"])
            stock["pnl_pct"] = round((spot - cost) / cost * 100 * (1 if sh > 0 else -1), 1)
            if sh < 0 and spot >= cost * 1.15:
                stock["flag"] = "short stock up >= 15% vs entry: stop hit"
            if sh > 0 and spot < cost:
                stock["flag"] = "held lot underwater: no new puts on this name"
        out["stock"] = stock
        if sh < 0 and any(lg["type"] == "short_put" for lg in legs):
            out["flag"] = "short stock against short puts (Anti-CAPR)"
    shorts = [lg for lg in legs if lg["type"] == "short_put"]
    longs = [lg for lg in legs if lg["type"] == "long_put"]
    if shorts and longs:
        out["hedge_ratio"] = round(sum(x["qty"] for x in longs) / sum(x["qty"] for x in shorts), 2)
    return out


# --------------------------------------------------------------------- floor

def treasury_stock_shares(instruments: list[dict], price: float) -> float:
    """Net new shares (M) from options/warrants in the money at `price`."""
    added = 0.0
    for ins in instruments:
        qty, strike = float(ins["qty_m"]), float(ins["strike"])
        if strike < price:
            added += qty - qty * strike / price
    return added


def floor(d: dict) -> dict:
    """Cash per fully diluted share, now and at an expiry.

    Required: cash ($M: cash + equivalents + marketable securities, no
    restricted cash), balance_sheet_date, as_of, basic_shares_m.
    Optional: inflows_since ($M, post-quarter cash incl. offering proceeds
    and asset sales), quarterly_burn ($M operating cash outflow, positive),
    debt ($M principal + exit fees, incl. royalty financing), other_claims
    ($M, anything else you choose to subtract), prefunded_warrants_m,
    issued_since_m, convertible_shares_m, dilutive [{qty_m, strike}],
    reference_price (usually the short-put strike), expiry.

    cash_per_share = (cash + inflows - burn since balance sheet) / FD shares,
    the convention the other audits use. net_of_debt_per_share also takes off
    debt and other_claims.
    """
    g = lambda k: float(d.get(k, 0) or 0)  # noqa: E731
    shares = (g("basic_shares_m") + g("prefunded_warrants_m") + g("issued_since_m")
              + g("convertible_shares_m"))
    if shares <= 0:
        raise ValueError("basic_shares_m must be positive")
    warnings = []
    if d.get("reference_price"):
        shares += treasury_stock_shares(d.get("dilutive", []), float(d["reference_price"]))
    elif d.get("dilutive"):
        warnings.append("dilutive instruments ignored: pass reference_price")
    burn_day = g("quarterly_burn") / 91.0
    elapsed = _days(d["balance_sheet_date"], d["as_of"])
    if elapsed > 120:
        warnings.append(f"balance sheet is {elapsed} days old: look for a newer 10-Q/10-K")
    cash_now = g("cash") + g("inflows_since") - burn_day * elapsed
    claims = g("debt") + g("other_claims")
    out = {
        "fd_shares_m": round(shares, 3),
        "days_since_balance_sheet": elapsed,
        "cash_now": round(cash_now, 2),
        "cash_per_share": round(cash_now / shares, 3),
        "net_of_debt_per_share": round((cash_now - claims) / shares, 3),
    }
    if d.get("expiry"):
        cash_exp = cash_now - burn_day * _days(d["as_of"], d["expiry"])
        out["cash_per_share_at_expiry"] = round(cash_exp / shares, 3)
        out["net_of_debt_per_share_at_expiry"] = round((cash_exp - claims) / shares, 3)
    if burn_day > 0:
        out["runway_months"] = round(max(cash_now, 0) / (burn_day * 30.4), 1)
    if warnings:
        out["warnings"] = warnings
    return out


COMMANDS = {"iv30": iv30, "overlay": overlay, "event_move": event_move,
            "event-move": event_move, "position": position, "floor": floor}


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[1] not in COMMANDS:
        print("usage: sentinel_calc.py {iv30|overlay|event_move|position|floor} '<json>'", file=sys.stderr)
        return 2
    raw = argv[2] if len(argv) > 2 else sys.stdin.read()
    print(json.dumps(COMMANDS[argv[1]](json.loads(raw)), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
