"""Deterministic math for the Biotech Ticker Sentinel.

Stdlib only. Every subcommand reads one JSON object (argument or stdin) and
prints one JSON object, so the model never does floor/IV/ledger arithmetic
in its head.

    python sentinel_calc.py floor '{"cash": 120.5, ...}'
    python sentinel_calc.py event-move '{"spot": 3.1, ...}'
    python sentinel_calc.py leg '{"spot": 3.1, "strike": 2.5, ...}'

Money inputs are in $M for `floor`, per-share/per-contract dollars elsewhere.
"""

from __future__ import annotations

import json
import math
import sys
from datetime import date

DAYS_PER_YEAR = 365.0
# Expected |move| of a normal variable is sqrt(2/pi) ~ 0.798 of its std dev.
ABS_MOVE_FACTOR = math.sqrt(2.0 / math.pi)


def _days(a: str, b: str) -> int:
    return (date.fromisoformat(b) - date.fromisoformat(a)).days


def treasury_stock_shares(instruments: list[dict], price: float) -> float:
    """Net new shares (M) from options/warrants that are in the money at `price`."""
    added = 0.0
    for ins in instruments:
        qty, strike = float(ins["qty_m"]), float(ins["strike"])
        if strike < price:
            added += qty - qty * strike / price
    return added


def cash_floor(d: dict) -> dict:
    """Gross and net cash per economic / fully diluted share.

    Required: cash ($M, cash + equivalents + marketable securities),
    balance_sheet_date, as_of, basic_shares_m.
    Optional: inflows_since ($M, post-quarter 8-K cash), debt ($M, principal
    plus exit/prepayment fees), current_liabilities ($M, AP + accrued, no
    deferred revenue), lease_liabilities ($M), refundable_deferred_revenue ($M),
    quarterly_burn ($M, operating cash outflow, positive number),
    prefunded_warrants_m, issued_since_m (ATM / 424B5 shares after cover date),
    convertible_shares_m, dilutive (list of {qty_m, strike}), reference_price
    (usually the short-put strike), expiry (ISO date).
    """
    g = lambda k: float(d.get(k, 0) or 0)  # noqa: E731
    liquid = g("cash") + g("inflows_since")
    claims = (g("debt") + g("current_liabilities") + g("lease_liabilities")
              + g("refundable_deferred_revenue"))
    burn_day = g("quarterly_burn") / 91.0

    econ = g("basic_shares_m") + g("prefunded_warrants_m") + g("issued_since_m")
    ref = d.get("reference_price")
    dil = econ + g("convertible_shares_m")
    if ref:
        dil += treasury_stock_shares(d.get("dilutive", []), float(ref))

    elapsed = _days(d["balance_sheet_date"], d["as_of"])
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
        to_exp = _days(d["as_of"], d["expiry"])
        net_exp = net_now - burn_day * to_exp
        out["net_cash_at_expiry"] = round(net_exp, 2)
        out["net_cash_per_share_at_expiry"] = round(net_exp / dil, 3)
    if burn_day > 0:
        out["runway_months_from_now"] = round(net_now / (burn_day * 30.4), 1)
    return out


def event_move(d: dict) -> dict:
    """Market-implied move for a binary event.

    Preferred: pre_iv (ATM IV of the last expiry before the event) and
    post_iv/post_dte (first expiry after it); IVs as decimals (3.08 = 308%).
    The pre-event IV stands in for base vol; the variance left over is the event.
    Fallback: straddle (ATM call + put mid of the first post-event expiry).
    """
    spot = float(d["spot"])
    out: dict = {}
    if d.get("pre_iv") and d.get("post_iv"):
        t2 = float(d["post_dte"]) / DAYS_PER_YEAR
        s1, s2 = float(d["pre_iv"]), float(d["post_iv"])
        event_var = s2 * s2 * t2 - s1 * s1 * t2
        out["term_structure_inverted"] = s2 > s1
        if event_var <= 0:
            out["event_std_move_pct"] = 0.0
            out["note"] = "post-event IV not above base: no event premium priced"
        else:
            std = math.sqrt(event_var)
            out["event_std_move_pct"] = round(std * 100, 1)
            out["expected_abs_move_pct"] = round(std * ABS_MOVE_FACTOR * 100, 1)
    if d.get("straddle"):
        pct = float(d["straddle"]) / spot
        out["straddle_move_pct"] = round(pct * 100, 1)
        out["straddle_low"] = round(spot * (1 - pct), 2)
        out["straddle_high"] = round(spot * (1 + pct), 2)
    if not out:
        raise ValueError("need pre_iv/post_iv/post_dte or straddle")
    if d.get("strike") and "expected_abs_move_pct" in out:
        down = spot * (1 - out["expected_abs_move_pct"] / 100)
        out["strike_inside_expected_down_move"] = float(d["strike"]) >= down
    return out


def leg(d: dict) -> dict:
    """Short put (or put spread) ledger row and Playbook v2 alarms.

    Required: spot, strike, credit (per share), qty, dte. Optional: mark
    (current mid to close), delta, long_strike (spread), nav, held_shares,
    other_name_exposure ($ already at risk on this name in other legs).
    """
    spot, k = float(d["spot"]), float(d["strike"])
    credit, qty, dte = float(d["credit"]), int(d["qty"]), int(d["dte"])
    long_k = d.get("long_strike")
    width = k - float(long_k) if long_k is not None else k
    max_loss = (width - credit) * 100 * qty
    intrinsic = max(0.0, k - spot)
    out = {
        "breakeven": round(k - credit, 3),
        "cushion_to_strike_pct": round((spot - k) / spot * 100, 1),
        "cushion_to_breakeven_pct": round((spot - (k - credit)) / spot * 100, 1),
        "intrinsic": round(intrinsic, 3),
        "assignment_notional": round(k * 100 * qty, 2),
        "max_loss": round(max_loss, 2),
    }
    alarms = []
    if spot < k:
        alarms.append("ITM")
    elif (spot - k) / spot <= 0.07:
        alarms.append("within 7% of strike")
    if d.get("delta") is not None and float(d["delta"]) <= -0.30:
        alarms.append("delta <= -0.30")
    if dte <= 21 and (spot - k) / spot <= 0.20:
        alarms.append("<= 21 DTE near the money")
    if d.get("mark") is not None:
        mark = float(d["mark"])
        out["captured_pct"] = round((credit - mark) / credit * 100, 1)
        if mark <= 0.05:
            alarms.append("dead collateral (mark <= $0.05): buy back")
        elif out["captured_pct"] >= 50:
            alarms.append(">= 50% captured: velocity take-profit")
        if intrinsic > 0 and mark < intrinsic:
            alarms.append("mark below intrinsic: quote stale or unfillable")
    if d.get("nav"):
        exposure = (float(d.get("held_shares", 0)) * spot + max_loss
                    + float(d.get("other_name_exposure", 0)))
        out["name_exposure_pct_nav"] = round(exposure / float(d["nav"]) * 100, 2)
        if out["name_exposure_pct_nav"] > 10:
            alarms.append("over 10% NAV cap")
    out["alarms"] = alarms
    return out


COMMANDS = {"floor": cash_floor, "event-move": event_move, "leg": leg}


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[1] not in COMMANDS:
        print(f"usage: sentinel_calc.py {{{'|'.join(COMMANDS)}}} '<json>'", file=sys.stderr)
        return 2
    raw = argv[2] if len(argv) > 2 else sys.stdin.read()
    print(json.dumps(COMMANDS[argv[1]](json.loads(raw)), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
