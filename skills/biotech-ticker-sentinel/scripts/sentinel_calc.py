"""Deterministic math for the Biotech Ticker Sentinel.

Stdlib only. Every subcommand reads one JSON object (argument, or stdin when
the argument is omitted) and prints one JSON object, so the model never does
floor/IV/ledger/date arithmetic in its head.

    python3 sentinel_calc.py overlay    '{"as_of": "2026-10-28", "event_date": "2026-11-22", ...}'
    python3 sentinel_calc.py event-move '{"spot": 3.1, "pre_iv": 1.4, ...}'
    python3 sentinel_calc.py book       '{"nav": 250000, "positions": [...]}'
    python3 sentinel_calc.py leg        '{"spot": 3.1, "strike": 2.5, ...}'
    python3 sentinel_calc.py floor      '{"cash": 120.5, ...}'

Money inputs are in $M for `floor`, per-share/per-contract dollars elsewhere.
IVs are decimals (3.08 = 308%). Dates are ISO (YYYY-MM-DD).
"""

from __future__ import annotations

import json
import math
import sys
from datetime import date, timedelta

DAYS_PER_YEAR = 365.0
# Expected |x| of a normal variable is sqrt(2/pi) ~ 0.798 of its std dev.
ABS_MOVE_FACTOR = math.sqrt(2.0 / math.pi)
NEAR_MONEY = 0.20  # cushion at or under which a <= 21 DTE leg needs action
DEFENSE_CUSHION = 0.07
DEFENSE_DELTA = -0.30
NAV_CAP_PCT = 10.0


def _d(s: str) -> date:
    return date.fromisoformat(s)


def _days(a: str, b: str) -> int:
    return (_d(b) - _d(a)).days


def _dte(d: dict) -> int:
    if d.get("dte") is not None:
        return int(d["dte"])
    return _days(d["as_of"], d["expiry"])


# --------------------------------------------------------------------------- floor

def treasury_stock_shares(instruments: list[dict], price: float) -> float:
    """Net new shares (M) from options/warrants that are in the money at `price`."""
    added = 0.0
    for ins in instruments:
        qty, strike = float(ins["qty_m"]), float(ins["strike"])
        if strike < price:
            added += qty - qty * strike / price
    return added


def cash_floor(d: dict) -> dict:
    """Gross and net cash per share, now and at an expiry.

    Required: cash ($M, cash + equivalents + marketable securities),
    balance_sheet_date, as_of, basic_shares_m.
    Optional: inflows_since ($M, post-quarter cash incl. ATM/offering proceeds
    and asset sales), debt ($M, principal plus exit/prepayment fees),
    current_liabilities ($M, AP + accrued, no deferred revenue),
    lease_liabilities ($M), refundable_deferred_revenue ($M),
    quarterly_burn ($M, operating cash outflow, positive number),
    prefunded_warrants_m, issued_since_m (shares issued after the cover date),
    convertible_shares_m, dilutive (list of {qty_m, strike}), reference_price
    (usually the short-put strike), expiry.
    Gross uses economic shares (basic + pre-funded + issued since); net uses
    fully diluted shares. Subtracting current liabilities on top of forward
    burn is deliberately conservative.
    """
    g = lambda k: float(d.get(k, 0) or 0)  # noqa: E731
    liquid = g("cash") + g("inflows_since")
    claims = (g("debt") + g("current_liabilities") + g("lease_liabilities")
              + g("refundable_deferred_revenue"))
    burn_day = g("quarterly_burn") / 91.0

    econ = g("basic_shares_m") + g("prefunded_warrants_m") + g("issued_since_m")
    if econ <= 0:
        raise ValueError("basic_shares_m must be positive")
    dil = econ + g("convertible_shares_m")
    warnings = []
    if d.get("reference_price"):
        dil += treasury_stock_shares(d.get("dilutive", []), float(d["reference_price"]))
    elif d.get("dilutive"):
        warnings.append("dilutive instruments ignored: pass reference_price")

    elapsed = _days(d["balance_sheet_date"], d["as_of"])
    if elapsed > 120:
        warnings.append(f"balance sheet is {elapsed} days old: check for a newer 10-Q/10-K")
    net_now = liquid - claims - burn_day * elapsed
    out = {
        "economic_shares_m": round(econ, 3),
        "fully_diluted_shares_m": round(dil, 3),
        "days_since_balance_sheet": elapsed,
        "gross_cash_per_share": round(liquid / econ, 3),
        "net_cash_now": round(net_now, 2),
        "net_cash_per_share_now": round(net_now / dil, 3),
    }
    if d.get("expiry"):
        net_exp = net_now - burn_day * _days(d["as_of"], d["expiry"])
        out["net_cash_at_expiry"] = round(net_exp, 2)
        out["net_cash_per_share_at_expiry"] = round(net_exp / dil, 3)
    if burn_day > 0:
        out["runway_months_net_of_claims"] = round(max(net_now, 0) / (burn_day * 30.4), 1)
    if warnings:
        out["warnings"] = warnings
    return out


# ------------------------------------------------------------------------- overlay

def overlay(d: dict) -> dict:
    """Classify expiries against a dated event or an open-ended window.

    Required: as_of, expiries (list), and either event_date or
    window_start + window_end. Statuses: before (scheduled date is after
    expiry; an early action can still land), ambiguous (event falls on a
    weekend/holiday right after this expiry; action may come before or after
    its close), carries (expiry is on/after the event), in_window (an
    open-ended window overlaps; may or may not carry).
    """
    as_of = _d(d["as_of"])
    expiries = sorted(_d(e) for e in d["expiries"])
    out: dict = {"expiries": []}
    if d.get("event_date"):
        ev = _d(d["event_date"])
        earliest = ev
        holidays = {_d(h) for h in d.get("holidays", [])}
        while earliest.weekday() >= 5 or earliest in holidays:
            earliest -= timedelta(days=1)
        if earliest != ev:
            out["note"] = (f"{ev} is not a trading day; action may come on or before "
                           f"{earliest} (FDA can also act early or miss the date)")
        for e in expiries:
            status = "before" if e < earliest else "ambiguous" if e < ev else "carries"
            out["expiries"].append({"expiry": e.isoformat(), "dte": (e - as_of).days, "status": status})
        pre = [e for e in expiries if e < earliest]
        post = [e for e in expiries if e >= ev]
    else:
        ws, we = _d(d["window_start"]), _d(d["window_end"])
        for e in expiries:
            status = "before" if e < ws else "carries" if e >= we else "in_window"
            out["expiries"].append({"expiry": e.isoformat(), "dte": (e - as_of).days, "status": status})
        pre = [e for e in expiries if e < ws]
        post = [e for e in expiries if e >= we]
    out["pre_event_expiry"] = pre[-1].isoformat() if pre else None
    out["post_event_expiry"] = post[0].isoformat() if post else None
    return out


# ---------------------------------------------------------------------- event-move

def event_move(d: dict) -> dict:
    """Market-implied move for a binary event, and whether a short put is paid.

    Preferred: pre_iv (ATM IV of the last expiry before the event) and
    post_iv + post_dte (or post_expiry + as_of) for the first expiry after it.
    The pre-event IV stands in for base vol; the variance left over is the
    event. Moves are in log space, so a 150% move gives a down level of
    spot * e^-1.5, never a negative price.
    Fallback: straddle (ATM call + put mid of the first post-event expiry);
    it also contains base vol to expiry, so it overstates the event alone.
    Optional strike (+ credit) returns the PAID / THIN / UNPAID verdict.
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
            out["note"] = "post-event IV not above base: no event premium priced"
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
    if d.get("strike") and down is not None:
        k = float(d["strike"])
        if d.get("credit") is not None:
            be = k - float(d["credit"])
            out["breakeven"] = round(be, 3)
            out["verdict"] = "PAID" if k <= down else "THIN" if be <= down else "UNPAID"
        else:
            out["strike_inside_expected_down_move"] = k > down
    return out


# ----------------------------------------------------------------------------- leg

def leg(d: dict) -> dict:
    """Short put (or bull put spread) ledger row and Playbook v2 alarms.

    Required: spot, strike, credit (per share), qty, and dte or expiry + as_of.
    Optional: mark (current mid to close the whole leg/spread), delta (of the
    short contract), long_strike (spread), nav, held_shares,
    other_name_exposure ($ at risk on this name outside this leg).
    Use `book` when a name has more than one leg.
    """
    spot, k = float(d["spot"]), float(d["strike"])
    credit, qty, dte = float(d["credit"]), int(d["qty"]), _dte(d)
    long_k = d.get("long_strike")
    width = k - float(long_k) if long_k is not None else k
    max_loss = (width - credit) * 100 * qty
    intrinsic = min(max(0.0, k - spot), width)
    cushion = (spot - k) / spot
    out = {
        "dte": dte,
        "breakeven": round(k - credit, 3),
        "cushion_to_strike_pct": round(cushion * 100, 1),
        "cushion_to_breakeven_pct": round((spot - (k - credit)) / spot * 100, 1),
        "intrinsic": round(intrinsic, 3),
        "assignment_notional": round(k * 100 * qty, 2),
        "max_loss": round(max_loss, 2),
    }
    alarms = []
    if spot < k:
        alarms.append("ITM")
    elif cushion <= DEFENSE_CUSHION:
        alarms.append("within 7% of strike")
    if d.get("delta") is not None and float(d["delta"]) <= DEFENSE_DELTA:
        alarms.append("delta <= -0.30")
    if dte <= 21 and cushion <= NEAR_MONEY:
        alarms.append("<= 21 DTE near the money")
    if d.get("mark") is not None:
        mark = float(d["mark"])
        out["captured_pct"] = round((credit - mark) / credit * 100, 1)
        if mark <= 0.05:
            alarms.append("dead collateral (mark <= $0.05): buy back")
        elif out["captured_pct"] >= 50:
            alarms.append(">= 50% captured: velocity take-profit")
        if intrinsic > 0 and mark < intrinsic - 0.005:
            alarms.append("mark below intrinsic: quote stale or unfillable")
    if d.get("nav"):
        exposure = (float(d.get("held_shares", 0)) * spot + max_loss
                    + float(d.get("other_name_exposure", 0)))
        out["name_exposure_pct_nav"] = round(exposure / float(d["nav"]) * 100, 2)
        if out["name_exposure_pct_nav"] > NAV_CAP_PCT:
            alarms.append("over 10% NAV cap")
    out["alarms"] = alarms
    return out


def book(d: dict) -> dict:
    """Ledger for the whole book, with name exposure counted once per ticker.

    Input: {nav, as_of?, positions: [{ticker, spot, held_shares?, legs: [leg
    fields without spot]}]}. Exposure = held shares * spot + sum of leg max
    losses, so the 10% NAV cap sees every leg and the shares together.
    """
    nav = float(d["nav"])
    rows = []
    for p in d["positions"]:
        spot = float(p["spot"])
        legs = []
        for lg in p.get("legs", []):
            args = {"as_of": d.get("as_of"), **lg, "spot": spot}
            legs.append({**{k: lg[k] for k in ("strike", "long_strike", "expiry") if k in lg}, **leg(args)})
        held_value = float(p.get("held_shares", 0)) * spot
        exposure = held_value + sum(x["max_loss"] for x in legs)
        pct = exposure / nav * 100
        name_alarms = ["over 10% NAV cap"] if pct > NAV_CAP_PCT else []
        if float(p.get("held_shares", 0)) < 0 and legs:
            name_alarms.append("Anti-CAPR: short stock against short puts")
        rows.append({
            "ticker": p["ticker"],
            "exposure": round(exposure, 2),
            "exposure_pct_nav": round(pct, 2),
            "name_alarms": name_alarms,
            "legs": legs,
        })
    rows.sort(key=lambda r: r["exposure"], reverse=True)
    return {"nav": nav, "names": rows}


COMMANDS = {"floor": cash_floor, "overlay": overlay, "event-move": event_move,
            "leg": leg, "book": book}


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[1] not in COMMANDS:
        print(f"usage: sentinel_calc.py {{{'|'.join(COMMANDS)}}} '<json>'", file=sys.stderr)
        return 2
    raw = argv[2] if len(argv) > 2 else sys.stdin.read()
    print(json.dumps(COMMANDS[argv[1]](json.loads(raw)), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
