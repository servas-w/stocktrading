#!/usr/bin/env python3
"""
underwrite.py - deterministic calculator for the large-cap-put-overreaction and
biotech-options-master-engine skills. One call replaces ~20 hand calculations.
Stdlib only. Missing inputs print 'n/a' or UNVERIFIED; the script never crashes on gaps.

  python3 underwrite.py strikes '{"spot":227.4,"iv":42,"dte":86,"inc":5}'
  python3 underwrite.py lc  '<json>'    # large-cap short put / bull put spread
  python3 underwrite.py bio '<json>'    # biotech tiers, floors, EV, Mode C, PoS, napkin DCF
  python3 underwrite.py lot '<json>'    # re-underwrite a held / assigned stock lot as a fresh entry
IV gate source ladder: ivr_src "ibkr" (primary; pass ivp_52w / ivp_26w / ivp_13w from IBKR get_price_snapshot) or
"barchart" are authoritative. IBKR gives IV Percentile, not IV Rank: the calculator converts it to an IVR-equivalent
= IVP52 - 10, so every IVR gate (30/35/40/50/70) maps to IVP52 (40/45/50/60/80). GREEN also needs IVP26 >= 50.
Proxy IVR (anything else) is auto-rejected when its ATM IV ("iv30") differs from the live chain's ATM IV ("atm_iv") by >30%.

JSON may be inline, a file path, or '-' for stdin.
Units: IVR/IVP in points (0-100). IV/HV as % (42) or decimal (0.42). div_yield in % points (2.9 = 2.9%).
Probabilities, haircuts, factors as decimals (0.25). Dollar totals in raw dollars.
"""
import json
import math
import sys
from datetime import date, datetime, timedelta

OK, NO, WARN, UNK = "PASS", "FAIL", "WARN", "UNVERIFIED"
# Unrisked value ladder for secondary programs when no program-level DCF exists (napkin, not disclosure)
STAGE_PV = {"preclinical": 1.5e7, "discovery": 1.5e7, "ind": 1.5e7,
            "ph1": 7.5e7, "phase1": 7.5e7, "ph1/2": 7.5e7, "phase1/2": 7.5e7,
            "ph2": 1.5e8, "phase2": 1.5e8, "ph2poc": 1.5e8,
            "ph3": 3.0e8, "phase3": 3.0e8}


# ---------- helpers ----------
def f(v):
    try:
        return None if v is None or v == "" else float(v)
    except (TypeError, ValueError):
        return None


def vol(v):
    v = f(v)
    return None if v is None else (v / 100.0 if v > 5 else v)


def prob(v):
    v = f(v)
    return None if v is None else (v / 100.0 if v > 1 else v)


def yld(v):
    """Dividend yield in PERCENT POINTS exactly as Robinhood reports it (2.9 = 2.9%, 0.12 = 0.12%)."""
    v = f(v)
    return None if v is None else v / 100.0


def ratio(v):
    """Run-ups etc.: decimal (1.2 = 120%); values > 5 are read as percent."""
    v = f(v)
    return None if v is None else (v / 100.0 if v > 5 else v)


def d(s):
    if not s:
        return None
    try:
        return datetime.strptime(str(s)[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def sessions_between(a, b):
    """Weekdays after a up to and including b (holidays ignored)."""
    if not a or not b or b <= a:
        return 0
    n, day = 0, a
    while day < b:
        day += timedelta(days=1)
        if day.weekday() < 5:
            n += 1
    return n


def m(x, dp=2):
    return "n/a" if x is None else f"{x:,.{dp}f}"


def p(x, dp=1):
    return "n/a" if x is None else f"{x * 100:.{dp}f}%"


def big(x):
    if x is None:
        return "n/a"
    a, sg = abs(x), ("-" if x < 0 else "")
    if a >= 1e9:
        return f"{sg}${a / 1e9:,.2f}B"
    if a >= 1e6:
        return f"{sg}${a / 1e6:,.1f}M"
    return f"{sg}${a:,.0f}"


def ncdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def put_delta(S, K, T, r, q, sig):
    if not all(v is not None for v in (S, K, T, sig)) or T <= 0 or sig <= 0 or S <= 0 or K <= 0:
        return None
    d1 = (math.log(S / K) + (r - q + 0.5 * sig * sig) * T) / (sig * math.sqrt(T))
    return -math.exp(-q * T) * ncdf(-d1)


def strike_for_delta(S, T, r, q, sig, target):
    lo, hi = 0.01 * S, S
    for _ in range(80):
        mid = (lo + hi) / 2
        dm = put_delta(S, mid, T, r, q, sig)
        if dm is None:
            return None
        if abs(dm) > abs(target):
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def leg(x):
    x = x or {}
    bid, ask = f(x.get("bid")), f(x.get("ask"))
    mid = f(x.get("mid"))
    if mid is None and bid is not None and ask is not None:
        mid = (bid + ask) / 2
    width = (ask - bid) / mid if (bid is not None and ask is not None and mid) else None
    return {"K": f(x.get("strike")), "bid": bid, "ask": ask, "mid": mid, "width": width,
            "delta": f(x.get("delta")), "iv": vol(x.get("iv")), "oi": f(x.get("oi"))}


def sell_fill(L):
    """Spread-width execution rule for SELLING: <=20% mid; 20-25% halfway to bid; >25% bid."""
    if L["mid"] is None:
        return None, "no quote"
    w = L["width"]
    if w is None or w <= 0.20:
        return L["mid"], "mid"
    if w <= 0.25 or L["bid"] is None:
        return (L["mid"] + (L["bid"] if L["bid"] is not None else L["mid"])) / 2, "mid-to-bid (20-25% wide)"
    return L["bid"], "bid (>25% wide)"


def buy_fill(L):
    if L["mid"] is None:
        return None, "no quote"
    w = L["width"]
    if w is None or w <= 0.20:
        return L["mid"], "mid"
    if w <= 0.25 or L["ask"] is None:
        return (L["mid"] + (L["ask"] if L["ask"] is not None else L["mid"])) / 2, "mid-to-ask (20-25% wide)"
    return L["ask"], "ask (>25% wide)"


def oi_gate(oi):
    if oi is None:
        return UNK
    # liquidity is information only: the user handles fills, so thin OI warns but never rejects
    return OK if oi >= 150 else WARN


def rule7(cls, default):
    """Playbook Rule 7 under-cost threshold by universe.md class: BIO/SC 15%, LC/MC 25%."""
    c = str(cls or default).upper()
    return c, (0.15 if c in ("BIO", "SC") else 0.25)


def exposure(x, S, K, add_contracts=1, default_cls="LC"):
    """Portfolio-aware check. x['existing'] = {shares, avg_cost, short_puts, short_calls, nav, max_name_pct}.
    Class (x['class'] or existing.class, from universe.md) sets the Rule 7 underwater threshold.
    Returns (lines, cap_reason or None). Cap reasons push the verdict to CONDITIONAL."""
    e = x.get("existing") or {}
    if not e:
        return ["Exposure: existing holdings not checked (pass 'existing') -> UNVERIFIED"], "existing exposure unchecked"
    cls, thr = rule7(x.get("class") or e.get("class"), default_cls)
    sh, avg = f(e.get("shares")) or 0.0, f(e.get("avg_cost"))
    # contract counts as magnitudes: "-7x Nov 2.5P" and 7 both mean 7 short puts
    sp, sc = abs(f(e.get("short_puts")) or 0.0), abs(f(e.get("short_calls")) or 0.0)
    nav, cap = f(e.get("nav")), prob(e.get("max_name_pct")) or 0.10
    eq_after = sh + 100 * (sp + add_contracts)          # share-equivalents if every put is assigned
    notional = sh * (S or 0) + 100 * (sp + add_contracts) * (K if K else (S or 0))
    pct = notional / nav if nav else None
    under = (avg is not None and S and sh > 0 and S < avg * (1 - thr))
    lines = [f"Exposure: hold {sh:,.0f} sh @ {m(avg)} ({p(S / avg - 1 if (avg and S) else None)} vs cost) | open short puts {sp:g}"
             f" | covered calls {sc:g} | if assigned: {eq_after:,.0f} sh-eq = {big(notional)}"
             f" = {p(pct)} of NAV (cap {p(cap)}) | class {cls}: Rule 7 blocks new puts > {p(thr, 0)} under cost"]
    reason = None
    if pct is not None and pct > cap:
        reason = f"name concentration {p(pct)} of NAV > {p(cap)} cap"
    if under:
        reason = (reason + "; " if reason else "") + (f"adds to an underwater lot (>{p(thr, 0)} below cost, {cls}, Rule 7):"
                                                       " run `lot` first, no averaging down")
    return lines, reason


def ivr_status(ivr):
    if ivr is None:
        return UNK
    return "GREEN" if ivr >= 50 else ("YELLOW" if ivr >= 30 else "RED")


IBKR_IVP_OFFSET = 10.0  # IVR-equivalent = IVP52 - 10 (IVP runs above IVR after vol spikes)


def firm(src):
    """Authoritative IV sources: IBKR snapshot (IVP) or Barchart (IVR). Everything else is a proxy."""
    s = str(src).lower()
    return "barchart" in s or "ibkr" in s


def pts(v):
    """IV percentile/rank in points; IBKR returns fractions (0.235 -> 23.5)."""
    v = f(v)
    if v is None:
        return None
    return v * 100.0 if abs(v) <= 1.0 else v


def resolve_iv(x):
    """Returns ivr, ivp, src, note, unconfirmed. IBKR IVP52 -> IVR-equivalent; IVP26 < 50 blocks a clean GREEN."""
    ivr, ivp, src = f(x.get("ivr")), pts(x.get("ivp")), x.get("ivr_src", "unstated")
    p13, p26, p52 = pts(x.get("ivp_13w")), pts(x.get("ivp_26w")), pts(x.get("ivp_52w"))
    if p52 is None and ivp is not None and "ibkr" in str(src).lower():
        p52 = ivp
    note, unconfirmed = "", False
    if "ibkr" in str(src).lower() and p52 is not None:
        if ivr is None:
            ivr = max(0.0, min(100.0, p52 - IBKR_IVP_OFFSET))
        ivp = p52
        note = (f" | IBKR IVP 13w {m(p13, 1)} / 26w {m(p26, 1)} / 52w {m(p52, 1)} -> IVR-eq {m(ivr, 1)}"
                f" (IVP52 - {IBKR_IVP_OFFSET:g})")
        if ivr >= 50 and p26 is not None and p26 < 50:
            unconfirmed = True
            note += " | 26w IVP < 50: regime unconfirmed -> max CONDITIONAL"
        if p26 is None and ivr >= 50:
            unconfirmed = True
            note += " | 26w IVP missing -> max CONDITIONAL"
    elif "ibkr" in str(src).lower():
        note = " | IBKR source but no ivp_52w passed -> UNVERIFIED"
    return ivr, ivp, src, note, unconfirmed


def proxy_flag(ivr, src, levels=(30, 35, 50)):
    if ivr is None:
        return False
    return not firm(src) and any(abs(ivr - lv) <= 5 for lv in levels)


def unchecked_proxy(ivr, src, proxy_iv, live_atm_iv):
    """Proxy IVR (not IBKR/Barchart) that cannot be cross-checked (proxy gave no ATM IV, or no live chain ATM IV)."""
    return ivr is not None and not firm(src) and not (proxy_iv and live_atm_iv)


def proxy_check(ivr, src, proxy_iv, live_atm_iv):
    """Reject a proxy IVR (not IBKR/Barchart) when the proxy's ATM IV disagrees with the live chain by >30% (junk-data guard)."""
    if unchecked_proxy(ivr, src, proxy_iv, live_atm_iv):
        return ivr, " | PROXY UNCHECKED (no ATM IV to cross-check) -> max CONDITIONAL"
    if ivr is None or firm(src) or not proxy_iv or not live_atm_iv:
        return ivr, ""
    dev = proxy_iv / live_atm_iv - 1
    if abs(dev) > 0.30:
        return None, f" | PROXY REJECTED: its ATM IV {proxy_iv * 100:.0f}% vs live chain {live_atm_iv * 100:.0f}% -> UNVERIFIED"
    return ivr, f" | proxy IV cross-check ok ({dev * 100:+.0f}%)"


def mark(s):
    return {"PASS": "\u2705", "FAIL": "\u274c", "WARN": "\u26a0\ufe0f", "UNVERIFIED": "\u2753"}.get(s, s)


def escalate(reasons):
    """Print a MODEL advisory. Fires on judgment calls the calculator can't check itself:
    unverified load-bearing inputs, soft/contested inputs (PoS, management tone), a trade
    about to size real capital, or a tier that rests on the calculator's own reasoning
    (Tier 1B, debt-netted floors) rather than a plain threshold. Never fires on a plain
    reject (RED IVR, Anti-ORCL, illiquid) - those need no judgment, just a pass."""
    reasons = [r for r in reasons if r]
    if reasons:
        print("MODEL: escalate to Opus - " + "; ".join(reasons))
    else:
        print("MODEL: Sonnet sufficient")


def load(arg):
    if arg == "-":
        return json.load(sys.stdin)
    if arg.strip().startswith("{"):
        return json.loads(arg)
    with open(arg) as fh:
        return json.load(fh)


# ---------- strikes ----------
def strikes(x):
    S, iv, dte = f(x.get("spot")), vol(x.get("iv")), f(x.get("dte"))
    r, q = f(x.get("r")) or 0.047, f(x.get("q")) or 0.0
    skew = f(x.get("skew")) or 1.15  # OTM put IV premium over ATM IV; use 1.0 if iv is already the OTM strike's IV
    inc = f(x.get("inc")) or (5.0 if (S or 0) >= 100 else (2.5 if (S or 0) >= 25 else 1.0))
    targets = x.get("deltas") or [-0.10, -0.125, -0.15]
    if None in (S, iv, dte):
        print("need spot, iv, dte")
        return
    T, sig = dte / 365.0, iv * skew
    print(f"spot {m(S)} | IV used {p(sig)} (ATM {p(iv)} x skew {skew}) | {int(dte)} DTE | inc {inc:g}")
    for t in targets:
        k = strike_for_delta(S, T, r, q, sig, t)
        lo = math.floor(k / inc) * inc
        hi = lo + inc
        print(f"  target d {t:+.3f} -> K* {m(k)} | listed {lo:g} (d {put_delta(S, lo, T, r, q, sig):+.3f}, "
              f"{p((S - lo) / S)} OTM) / {hi:g} (d {put_delta(S, hi, T, r, q, sig):+.3f})")
    wl, wh = 0.40 * S, 0.60 * S
    print(f"  wing zone (40-60% below spot): {m(wl)} - {m(wh)}")


# ---------- large cap ----------
def lc(x):
    T_ = x.get("ticker", "?")
    asof = d(x.get("asof")) or date.today()
    S = f(x.get("spot"))
    exp = d(x.get("exp"))
    dte = (exp - asof).days if exp else None
    ivr, ivp, src, ib_note, ib_unconf = resolve_iv(x)
    iv30, hv20 = vol(x.get("iv30")), vol(x.get("hv20"))
    sh, W = leg(x.get("short")), leg(x.get("wing")) if x.get("wing") else None
    mcap = f(x.get("mcap"))
    if mcap is None and f(x.get("shares")) and S:
        mcap = f(x.get("shares")) * S
    ocf, capex, sbc = f(x.get("ocf_ttm")), f(x.get("capex_ttm")), f(x.get("sbc_ttm"))
    fcf_fwd, capex_surge = f(x.get("fcf_fwd")), bool(x.get("capex_surge"))
    cash, debt = f(x.get("cash")), f(x.get("debt"))
    pe, dy, low52 = f(x.get("pe")), yld(x.get("div_yield")), f(x.get("low_52w"))
    missing, gates = [], []

    print(f"{T_} | asof {asof} | spot {m(S)} | exp {exp or 'n/a'} ({dte if dte is not None else 'n/a'} DTE"
          f"{'' if dte is None else (' in 60-90' if 60 <= dte <= 90 else ' OUTSIDE 60-90')})")

    unchecked = unchecked_proxy(ivr, src, iv30, vol(x.get("atm_iv")))
    ivr, pc_note = proxy_check(ivr, src, iv30, vol(x.get("atm_iv")))
    st = ivr_status(ivr)
    near = proxy_flag(ivr, src) or unchecked or ib_unconf
    ivhv = (iv30 / hv20) if (iv30 and hv20) else None
    print(f"IVR {m(ivr, 1)} (IVP {m(ivp, 1)}) src: {src} -> {st}{pc_note}{ib_note}"
          f"{' | near gate on proxy -> confirm on IBKR IVP' if proxy_flag(ivr, src) else ''}"
          f"{'' if ivhv is None else f' | IV30/HV20 {ivhv:.2f}' + (' WARN realized > implied' if ivhv < 1 else '')}")
    if ivr is None:
        missing.append("ivr")
    gates.append(("IV Rank", {"GREEN": OK, "YELLOW": WARN, "RED": NO}.get(st, UNK), st))

    last_er, next_er = d(x.get("last_earnings")), d(x.get("next_earnings"))
    since = sessions_between(last_er, asof) if last_er else None
    orcl = NO if (since is not None and since <= 10 and ivr is not None and ivr < 35) else OK
    if since is None:
        orcl = UNK if (ivr is None or ivr < 35) else OK
    gates.append(("Anti-ORCL", orcl, f"{since} sessions since ER" if since is not None else "last ER n/a"))
    runway = "n/a"
    if next_er and exp:
        runway = "CLEAN" if next_er > exp else "HAZARD (spans earnings)"
    print(f"Earnings: last {last_er or 'n/a'} ({since if since is not None else 'n/a'} sessions) | next {next_er or 'n/a'} -> {runway}"
          f"{' | NOTE: IV/IVR include the earnings-event premium; expect a post-ER crush (Anti-ORCL applies after)' if runway.startswith('HAZARD') else ''}")
    gates.append(("Earnings runway", OK if runway == "CLEAN" else (WARN if runway.startswith("HAZARD") else UNK), runway))

    # forensics
    fcf = (ocf - capex) if (ocf is not None and capex is not None) else None
    owner = (fcf - sbc) if (fcf is not None and sbc is not None) else None
    oy = owner / mcap if (owner is not None and mcap) else None
    dev = debt / (mcap + debt - (cash or 0)) if (debt is not None and mcap) else None
    req = 0.15
    why = ["base 15%"]
    universe = OK if mcap is not None else UNK
    if mcap is not None and mcap < 20e9:
        if mcap < 5e9:
            universe = NO
            why.append("mcap < $5B: out of universe")
        else:
            req = max(req, 0.25)
            why.append("mid-cap floor 25%")
            if ocf is None:
                universe = UNK
                why.append("mid-cap: OCF > 0 still to verify")
            elif ocf <= 0:
                universe = NO
                why.append("mid-cap needs OCF > 0")
    # TTM owner FCF <= 0 is already a hard reject; the 30% cushion is for a forward CapEx surge on a name that still passes
    if (fcf_fwd is not None and fcf_fwd < 0) or capex_surge:
        req = max(req, 0.30)
        why.append("forward FCF<0 / CapEx surge -> 30%")
    if dev is not None and dev > 0.25:
        req = req * (1 + 1.5 * dev)
        why.append(f"D/EV {p(dev)} >25% -> x{1 + 1.5 * dev:.2f}")
    solv = "n/a"
    if owner is not None:
        solv = "PASS (owner FCF > 0)" if owner > 0 else "FAIL (negative owner cash flow / SBC dilution)"
    print(f"Forensics: OCF {big(ocf)} - CapEx {big(capex)} - SBC {big(sbc)} = owner FCF {big(owner)} "
          f"(yield {p(oy)}) | cash {big(cash)} debt {big(debt)} D/EV {p(dev)} | mcap {big(mcap)} | solvency {solv}")
    gates.append(("Universe", universe, "mcap " + big(mcap)))
    # owner FCF <= 0 fails as a fresh entry, same rule as `lot` (financials pass no OCF -> UNVERIFIED, not a fail)
    owner_gate = UNK if owner is None else (OK if owner > 0 else NO)
    gates.append(("Owner FCF", owner_gate, big(owner)))

    # short leg
    credit_csp, how = sell_fill(sh)
    K = sh["K"]
    otm = (S - K) / S if (S and K) else None
    dlt = sh["delta"]
    if dlt is None and S and K and dte and sh["iv"]:
        dlt = put_delta(S, K, dte / 365.0, f(x.get("r")) or 0.047, dy or 0.0, sh["iv"])
    pot = min(1.0, 2 * abs(dlt)) if dlt is not None else None
    print(f"Short {m(K)}P: bid {m(sh['bid'])} ask {m(sh['ask'])} mid {m(sh['mid'], 3)} | width "
          f"{p(sh['width'])} -> fill {m(credit_csp, 3)} ({how}) | d {m(dlt, 3)}"
          f"{'' if dlt is None or -0.15 <= dlt <= -0.10 else ' (outside -0.10..-0.15)'} | OTM {p(otm)} | "
          f"PoT {p(pot)} | P(OTM) {p(None if dlt is None else 1 - abs(dlt))} | OI {m(sh['oi'], 0)}")
    cush_ok = UNK if otm is None else (OK if otm >= req else NO)
    gates.append(("Strike cushion", cush_ok, f"OTM {p(otm)} vs req {p(req)} [{'; '.join(why)}]"))
    gates.append(("Liquidity (short)", oi_gate(sh["oi"]), f"OI {m(sh['oi'], 0)}, width {p(sh['width'])}"))
    max_k = S * (1 - req) if S else None

    structure = "CSP"
    net = be = roc = width = None
    wing_ratio = None
    if W and W["K"] is not None:
        wing_ask = W["ask"] if W["ask"] is not None else W["mid"]
        wing_ratio = wing_ask / sh["mid"] if (wing_ask is not None and sh["mid"]) else None
        wz = (S - W["K"]) / S if S else None
        in_zone = wz is not None and 0.40 <= wz <= 0.60
        verdict_w = "n/a" if wing_ratio is None else ("<=5% -> CONVERT TO SPREAD (mandate)" if wing_ratio <= 0.05
                                                        else ">5% -> optional; CSP acceptable")
        print(f"Wing {m(W['K'])}P ({p(wz)} below spot{'' if in_zone else ' - outside 40-60% zone'}): ask {m(wing_ask)} "
              f"-> wing/credit {p(wing_ratio)} {verdict_w}")
        if wing_ratio is not None and (wing_ratio <= 0.05 or x.get("force_spread")):
            structure = "SPREAD"
            width = K - W["K"]
            net_mid = sh["mid"] - (W["mid"] if W["mid"] is not None else wing_ask)
            net = (credit_csp or sh["mid"]) - wing_ask
            be = K - net
            risk = width - net
            roc = net / risk * 365 / dte if (risk and dte) else None
            print(f"Spread {m(K)}/{m(W['K'])}: net credit mid {m(net_mid, 3)} | conservative {m(net, 3)} | "
                  f"max risk {m(risk * 100, 0)}/ct | BE {m(be)} (cushion {p((S - be) / S if S else None)}) | "
                  f"ROC {p(roc)} ann on max risk")
    be_csp = K - credit_csp if (K is not None and credit_csp is not None) else None
    roc_csp = credit_csp / (K - credit_csp) * 365 / dte if (be_csp and dte) else None
    regt = None
    if S and K and credit_csp is not None and dte:
        req_m = max(0.20 * S - max(0.0, S - K), 0.10 * K)
        regt = credit_csp / req_m * 365 / dte if req_m > 0 else None
    print(f"CSP: BE {m(be_csp)} (cushion {p((S - be_csp) / S if (S and be_csp) else None)}) | "
          f"ROC {p(roc_csp)} ann on cash | Reg-T est {p(regt)} ann")
    if structure == "CSP":
        net, be, roc = credit_csp, be_csp, roc_csp

    # fundamental floor checks (information)
    shares = f(x.get("shares")) or ((mcap / S) if (mcap and S) else None)
    if be is not None and owner and owner > 0 and shares:
        ev_be = be * shares + (debt or 0) - (cash or 0)
        print(f"Floor check: BE-implied EV/owner-FCF {ev_be / owner:.1f}x"
              f"{'' if low52 is None else f' | BE vs 52w low {m(low52)}: ' + ('below' if be <= low52 else 'ABOVE')}")
    elif low52 is not None and be is not None:
        print(f"Floor check: BE {'below' if be <= low52 else 'ABOVE'} 52w low {m(low52)}")
    # VALU handoff (stock-valuation-engine): BE above the valuation floor caps the verdict at CONDITIONAL
    vfloor, vig = f(x.get("val_floor")), f(x.get("val_implied_g"))
    val_cap = None
    if vfloor is not None and be is not None:
        val_ok = be <= vfloor
        gates.append(("VALU floor", OK if val_ok else WARN, f"BE {m(be)} vs floor {m(vfloor)}"))
        if not val_ok:
            val_cap = f"BE {m(be)} above VALU floor {m(vfloor)}"
        print(f"VALU: floor {m(vfloor)} -> BE {'at/below' if val_ok else 'ABOVE'} | price implies "
              f"{p(vig)} owner-FCF growth/yr")

    # scenarios + management
    if net is not None:
        bull, base = 0.70 * net * 100, 0.50 * net * 100
        if structure == "SPREAD":
            bear = -(width - net) * 100
            bear_s = f"-${abs(bear):,.0f} max loss (wing caps it)"
        else:
            mk = 0.60 * S if S else None
            bear = -(K - mk - net) * 100 if (mk and K) else None
            bear_s = f"-${abs(bear):,.0f} at a -40% mark (uncapped below)" if bear is not None else "n/a"
        print(f"Scenarios/ct: Bull +${bull:,.0f} (70% quick win) | Base +${base:,.0f} (50% GTC) | Bear {bear_s}")
        t21 = exp - timedelta(days=21) if exp else None
        print(f"Manage: GTC BTC @ {m(net * 0.5, 2)} | quick-win {m(net * 0.35, 2)}-{m(net * 0.25, 2)} if <=14d | "
              f"21-DTE exit {t21 or 'n/a'} | defense: spot <= {m(K * 1.07 if K else None)} or d <= -0.30 -> roll out "
              f"30-60d for a net credit")

    exp_lines, exp_cap = exposure(x, S, K)
    for ln in exp_lines:
        print(ln)

    # verdict
    yellow_ok = structure == "SPREAD" or (pe is not None and 0 < pe < 10) or (dy is not None and dy > 0.035)
    if st == "RED":
        v = "REJECTED (NO-GO) -> PULLBACK WATCHLIST: re-check when IVR >= 50 (IBKR IVP52 >= 60)"
    elif orcl == NO:
        v = "REJECTED (NO-GO): post-earnings IV scrap (Anti-ORCL)"
    elif universe == NO:
        v = "REJECTED (NO-GO): outside universe / mid-cap without positive OCF"
    elif owner_gate == NO:
        v = "REJECTED (NO-GO): owner FCF <= 0 (OCF - CapEx - SBC) - SBC dilution / burn, equity has no cash floor"
    elif S is None or K is None:
        v = "INCOMPLETE: IVR gate not failed - pull the chain (use `strikes`) and rerun with the short leg"
    elif cush_ok == NO:
        v = f"REJECTED at this strike -> move to <= {m(max_k)} (required cushion {p(req)})"
    elif st == "YELLOW":
        v = "CONDITIONAL (Hedged Only)" if yellow_ok else "REJECTED unless converted to a defined-risk spread"
    elif st == "UNVERIFIED":
        v = "CONDITIONAL: confirm IBKR IVP52 >= 60 and IVP26 >= 50 (or Barchart IVR >= 50) before entry"
    else:
        v = "SELL PUT SPREAD (Prime)" if structure == "SPREAD" else "SELL PUT - cash-secured (Prime)"
        if near:
            v = "CONDITIONAL: " + v + (" - proxy IVR unchecked, confirm on IBKR IVP" if unchecked
                                       else (" - IBKR 26w IVP not confirming" if ib_unconf
                                             else " - proxy IVR near gate, confirm on IBKR IVP"))
    if exp_cap and v.startswith(("SELL", "CONDITIONAL")):
        v = ("CONDITIONAL: " + v if v.startswith("SELL") else v) + f" - EXPOSURE: {exp_cap}"
    if val_cap and v.startswith(("SELL", "CONDITIONAL")):
        v = ("CONDITIONAL: " + v if v.startswith("SELL") else v) + f" - {val_cap}: go lower or skip"
    if universe == UNK and v.startswith("SELL"):
        v = "CONDITIONAL: " + v + " - universe unverified (mcap / mid-cap OCF)"
    if runway.startswith("HAZARD") and v.startswith(("SELL", "CONDITIONAL")):
        v += " | spans earnings: prefer the spread"
    print("GATES: " + " | ".join(f"{n} {mark(s)} {note}" for n, s, note in gates))
    if missing:
        print("MISSING (load-bearing): " + ", ".join(missing))
    print("VERDICT: " + v)
    # A hard, mechanical reject leaves nothing for a model to weigh - the softer judgment
    # calls (forensics gaps, YELLOW carve-outs, an unconfirmed proxy) are moot once the
    # trade is already dead on IVR, Anti-ORCL, universe, cushion, liquidity, or a missing chain.
    hard_reject = v.startswith(("REJECTED (NO-GO)", "REJECTED at this strike", "REJECTED: illiquid", "INCOMPLETE"))
    trading = v.startswith(("SELL", "CONDITIONAL"))
    escalate([
        "IVR unverified" if "ivr" in missing else None,
        "IV gate resting on an unconfirmed proxy" if (near and not hard_reject) else None,
        "market-cap/mid-cap universe unverified" if (universe == UNK and not hard_reject) else None,
        "owner FCF forensics incomplete (OCF/CapEx/SBC gap) - solvency unverified" if (owner is None and not hard_reject) else None,
        "YELLOW IV band: carve-out (PE/div or spread) is a judgment call" if (st == "YELLOW" and not hard_reject) else None,
        "sizing real capital - final check before the order" if trading else None,
    ])


# ---------- biotech ----------
def bio(x):
    T_ = x.get("ticker", "?")
    asof = d(x.get("asof")) or date.today()
    S = f(x.get("spot"))
    exp = d(x.get("exp"))
    dte = (exp - asof).days if exp else None
    ivr, _ivp, src, ib_note, ib_unconf = resolve_iv(x)
    cash, sti, restr = f(x.get("cash")) or 0.0, f(x.get("st_inv")) or 0.0, f(x.get("restricted")) or 0.0
    debt, cov = f(x.get("debt")) or 0.0, f(x.get("covenant_min")) or 0.0
    basic = f(x.get("basic_shares"))
    pfw = f(x.get("pfw"))  # None = not passed (UNKNOWN); 0 = verified none in the 10-Q equity note
    ssrc = str(x.get("shares_src") or "unstated")
    rh_src = any(k in ssrc.lower() for k in ("robinhood", "fundamentals"))
    fd = None
    if basic:
        fd = basic + (pfw or 0) + (f(x.get("penny_warrants")) or 0) + (f(x.get("pref_as_converted")) or 0)
    caps = []  # reasons that cap any APPROVED verdict at CONDITIONAL
    ocf = f(x.get("ocf_ttm"))
    qb = f(x.get("q_burn"))
    if qb is None and ocf is not None:
        qb = max(0.0, -ocf / 4.0)
    gross = cash + sti - restr
    net_liq = gross - debt
    raw_ps = gross / fd if fd else None
    net_ps = net_liq / fd if fd else None
    # qb == 0 means cash-generative (OCF >= 0): runway is unlimited, not unknown
    runway = gross / (qb / 3.0) if qb else (float("inf") if qb == 0 else None)
    adv = f(x.get("adv20"))
    wet = qb / (adv * S * 63) if (qb and adv and S) else None
    missing, gates = [], []
    if not fd:
        missing.append("basic_shares (+PFW)")
    if qb is None:
        missing.append("ocf_ttm or q_burn")
    if basic and pfw is None:
        missing.append("pfw (10-Q equity note / post-quarter 8-K; pass 0 only if verified none)")
        caps.append("FD share count unverified (pfw not passed)")

    print(f"{T_} | asof {asof} | spot {m(S)} | exp {exp or 'n/a'} ({dte if dte is not None else 'n/a'} DTE)")
    if basic:
        print(f"Shares: basic {m(basic / 1e6, 1)}M + PFW {'?' if pfw is None else m(pfw / 1e6, 1) + 'M'}"
              f" (+ penny/pref as passed) -> FD {m(fd / 1e6, 1)}M | src: {ssrc}"
              + ("" if pfw is not None else
                 " | \u26a0\ufe0f PFW UNVERIFIED -> per-share floors are overstated if any exist"
                 + (" (Robinhood fundamentals EXCLUDE pre-funded warrants)" if rh_src else "")))
    print(f"Cap table: FD shares {m(fd / 1e6 if fd else None, 1)}M | gross liquid {big(gross)} -> raw cash/sh "
          f"{m(raw_ps)} | debt {big(debt)} -> net cash/sh {m(net_ps)} | spot/net cash "
          f"{m(S / net_ps if (S and net_ps and net_ps > 0) else None, 1)}x")
    print(f"Burn: Q burn {big(qb)} | runway {m(runway, 1)} mo | ATM wet blanket "
          f"{p(wet)}{'' if wet is None else (' HIGH (>15%): ATM ceiling' if wet > 0.15 else ' ok')}")

    # catalyst / mode
    c = x.get("catalyst") or {}
    ws, we = d(c.get("window_start")), d(c.get("window_end")) or d(c.get("window_start"))
    buf = (ws - exp).days if (ws and exp) else None
    slipped = bool(c.get("guidance_slipped"))
    if ws is None or exp is None:
        mode = "UNKNOWN"
        missing.append("catalyst window / expiry")
    elif exp >= ws:
        mode = "B"
    elif buf >= 14 and not slipped:
        mode = "A"
    else:
        mode = "B*"  # expires <14d before window or timeline slipped -> Tier 1 standards
    days_to_end = (we - asof).days if we else None
    q_to_cat = max(1.0, days_to_end / 91.25) if days_to_end else 1.0
    print(f"Catalyst: {c.get('type', 'n/a')} window {ws or 'n/a'}..{we or 'n/a'} | expiry buffer "
          f"{buf if buf is not None else 'n/a'}d{' | TIMELINE SLIPPED' if slipped else ''} -> MODE {mode}"
          f"{' (pre-catalyst harvest, Tier 2 standards)' if mode == 'A' else ''}"
          f"{' (event exposure, Tier 1 standards)' if mode.startswith('B') else ''}")

    # floors
    a1 = max(0.0, (net_liq - (qb or 0) * (dte or 0) / 90.0 * 1.2) / fd) if fd else None
    a2 = max(0.0, (net_liq - (qb or 0) * 1.5 * q_to_cat) / fd) if fd else None
    trap = bool(x.get("accel_on_failure")) and gross <= debt + cov
    if trap:
        a2 = 0.0
    # pipeline SOTP: secondary programs always; the lead only under the de-risked lead exception
    resid, resid_lead, sotp = 0.0, 0.0, []
    eff_in_window = c.get("efficacy_readout") is not False  # missing -> assume an efficacy binary (conservative)
    for a in x.get("pipeline") or []:
        stg = str(a.get("stage", "")).lower().replace(" ", "").replace("_", "").replace("-", "")
        pv = f(a.get("pv"))
        lead_in = False
        if a.get("lead"):
            # De-risked lead exception: positive pivotal data AND no efficacy readout inside the contract
            if a.get("pivotal_positive") and not eff_in_window:
                pv = STAGE_PV["ph3"]  # floor uses the Phase 3 rung; napkin DCF replaces it in Base/Bull
                lead_in = True
                a = dict(a, name=f"{a.get('name', 'lead')} [de-risked lead @ Ph3 rung]")
            else:
                why = "no positive pivotal data" if not a.get("pivotal_positive") else "efficacy readout inside contract"
                sotp.append(f"{a.get('name', 'lead')} EXCLUDED (lead: {why})")
                continue
        if pv is None:
            pv = STAGE_PV.get(stg, 0.0)
        keep = 0.55 if a.get("partnered") else 0.175
        resid += pv * keep
        if lead_in:
            resid_lead += pv * keep
        sotp.append(f"{a.get('name', stg or '?')} {big(pv)}{' P' if a.get('partnered') else ''} x{keep:g} = {big(pv * keep)}")
    resid_ps = resid / fd if fd else 0.0
    burn_a, burn_b = (qb or 0) * (dte or 0) / 90.0 * 1.2, (qb or 0) * 1.5 * q_to_cat
    # Debt and the burn to the catalyst both rank ahead of equity: the pipeline fills any cash hole
    # (net debt OR net cash < burn) before it adds to the floor. Without a hole this equals A + SOTP/sh.
    netted = bool(fd) and (trap or net_liq < 0 or net_liq - burn_a < 0 or net_liq - burn_b < 0)
    anchor_a = max(0.0, (net_liq - burn_a + resid) / fd) if fd else None
    anchor_b = max(0.0, (net_liq - burn_b + resid) / fd) if fd else None
    print(f"Floors: A1 pre-catalyst {m(a1)} | A2 distressed (1.5x burn, {q_to_cat:.1f}q) {m(a2)}"
          f"{' [DEBT ACCELERATION TRAP -> 0]' if trap else ''} | SOTP residual {m(resid_ps)}/sh "
          f"-> FLOOR A (A1+SOTP) {m(anchor_a)} / FLOOR B (A2+SOTP) {m(anchor_b)}"
          f"{' [SOTP netted against the debt / burn hole first]' if netted else ''}")
    if sotp:
        print("SOTP: " + " | ".join(sotp) + f" -> {big(resid)} ({m(resid_ps)}/sh)")

    unchecked = unchecked_proxy(ivr, src, vol(x.get("iv30")), vol(x.get("atm_iv")))
    ivr, pc_note = proxy_check(ivr, src, vol(x.get("iv30")), vol(x.get("atm_iv")))
    ivst = ivr_status(ivr)
    near = proxy_flag(ivr, src, (40, 50, 70)) or unchecked or ib_unconf
    print(f"IVR {m(ivr, 1)} src: {src} -> {ivst}{pc_note}{ib_note}{' | near gate on proxy -> confirm on IBKR IVP' if proxy_flag(ivr, src, (40, 50, 70)) else ''}")

    mg = str(x.get("mgmt", "n/a")).upper()
    min_otm = 0.50 if mg == "YELLOW" else 0.35
    verdict_put = None
    b_tier = None
    sh = leg(x.get("short")) if x.get("short") else None
    pos = prob(x.get("pos"))
    pm = x.get("pos_model")
    if pm:
        base_p = prob(pm.get("baseline"))
        prod = 1.0
        for fac in pm.get("factors", []):
            prod *= (1 + f(fac))
        pos = base_p * prod if base_p is not None else pos
        cap = prob(pm.get("cap"))
        if cap is not None and pos is not None:
            pos = min(pos, cap)
        print(f"PoS model: baseline {p(base_p)} x prod(1+f) {prod:.3f}{'' if cap is None else f' cap {p(cap)}'} "
              f"-> {p(pos)}")
    if x.get("p_statsig") is not None:
        ps = prob(x.get("p_statsig"))
        print(f"Dual hurdle: P(stat-sig) {p(ps)} -> P(approval) {p(ps * 0.7)} (marginal design: -30%)")
    # Event PoS (the binary inside the contract) drives binary EV and Mode C only.
    # The lead DCF is risk-adjusted by its cumulative odds of reaching approval (LoA) - a different, smaller number.
    loa, loa_src = prob(x.get("pos_loa")), "pos_loa"
    if loa is None and x.get("pos_loa_after"):  # transitions AFTER the in-contract event; event PoS multiplied in here
        chain = [prob(v) for v in x.get("pos_loa_after") if prob(v) is not None]
        if chain and pos is not None:
            loa = pos
            for v in chain:
                loa *= v
            loa_src = f"event {p(pos)} x " + " x ".join(p(v, 0) for v in chain)
        elif chain:
            print("PoS split: pos_loa_after given but no event PoS -> LoA n/a")
    if loa is not None:
        print(f"PoS split: event {p(pos)} (binary EV, Mode C) | lead LoA {p(loa)} ({loa_src}) (DCF only)"
              + (" | \u26a0\ufe0f LoA > event PoS: approval normally requires passing the in-contract event - check"
                 if (pos is not None and loa > pos + 1e-9) else ""))

    if sh and sh["K"] is not None:
        uf = f((x.get("short") or {}).get("fill"))
        if uf is not None:
            credit, how = uf, "your fill"
        elif sh["mid"] is not None and (sh["bid"] or 0) > 0 and (sh["width"] is None or sh["width"] <= 1.0):
            credit, how = sh["mid"], "mid - pass short.fill for your actual fill"
        else:
            credit, how = None, "no two-sided market (0 bid / stub ask) - mid is meaningless, pass short.fill"
        K = sh["K"]
        if dte and K:
            need = K * 0.25 * dte / 365 / (1 + 0.25 * dte / 365)
            print(f"Min credit for 25% ann ROC on cash at {m(K)}P, {dte} DTE: {m(need, 3)}")
        be = K - credit if credit is not None else None
        otm = (S - K) / S if S else None
        dl = sh["delta"]
        roc = credit / (K - credit) * 365 / dte if (credit is not None and dte and K > credit) else None
        print(f"Short {m(K)}P: credit {m(credit, 3)} ({how}) | BE {m(be, 3)} | OTM {p(otm)} | d {m(dl, 3)} | "
              f"ROC {p(roc)} ann on cash"
              f"{'' if roc is None else (' (>=25% target)' if roc >= 0.25 else ' (below 25% target)')}")
        if S and K > S and credit is not None:
            intr = K - S
            extr = credit - intr
            roc_x = extr / (K - credit) * 365 / dte if (dte and K > credit) else None
            print(f"ITM by {p((K - S) / S)}: intrinsic {m(intr, 3)} + extrinsic {m(extr, 3)} -> ROC on extrinsic "
                  f"{p(roc_x)} ann | synthetic long at BE {m(be, 3)}, not a premium harvest")
        g = []
        if mode == "A":
            boost = 0.11 if (ivr or 0) >= 70 else (0.065 if (ivr or 0) >= 50 else 0.0)
            pop0 = 1 - abs(dl) if dl is not None else None
            pop = min(0.95, pop0 + boost) if pop0 is not None else None
            loss = max(0.0, K - credit - a1) if (credit is not None and a1 is not None) else None
            ev = pop * credit - (1 - pop) * loss if (pop is not None and loss is not None) else None
            ev0 = pop0 * credit - (1 - pop0) * loss if (pop0 is not None and loss is not None) else None
            print(f"PoP: d-only {p(pop0)} -> IV-edge {p(pop)} | EV/ct {m(ev * 100 if ev is not None else None, 0)} "
                  f"(d-only {m(ev0 * 100 if ev0 is not None else None, 0)}) | loss-at-floor {m(loss, 3)}/sh")
            g += [("BE<=anchor A", OK if (be is not None and anchor_a is not None and be <= anchor_a) else NO,
                   f"{m(be, 3)} vs {m(anchor_a)}"),
                  ("K<=raw cash/sh", OK if (raw_ps is not None and K <= raw_ps) else NO, f"{m(K)} vs {m(raw_ps)}"),
                  ("Runway>12m", OK if (runway is not None and runway > 12) else NO, f"{m(runway, 1)} mo"),
                  (f"OTM>={int(min_otm * 100)}%", OK if (otm is not None and otm >= min_otm) else NO, p(otm)),
                  ("EV>0", OK if (ev is not None and ev > 0) else NO, m(ev * 100 if ev is not None else None, 0))]
            tier_ok_name = "APPROVED: TIER 2 PRE-CATALYST HARVEST PUT"
        elif mode.startswith("B"):
            loss = max(0.0, K - anchor_b - credit) if (credit is not None and anchor_b is not None) else None
            ev = pos * credit - (1 - pos) * loss if (pos is not None and loss is not None) else None
            print(f"Binary EV: PoS {p(pos)} | loss-if-fail {m(loss, 3)}/sh | EV/ct {m(ev * 100 if ev is not None else None, 0)}"
                  f"{'' if pos is not None else ' (PoS needed: run references/deep-diligence.md)'}")
            if pos is None:
                missing.append("pos (Mode B)")
            # Gate on break-even, not strike. K<=Floor B -> Tier 1 | BE<=Floor B<K, OTM -> Tier 1B (lower tier)
            # | BE<=Floor B<K, ITM -> synthetic long, not a harvest | BE>Floor B -> Tier 3
            k_ok = anchor_b is not None and K <= anchor_b
            itm = S is not None and K > S
            hurdle = (K - anchor_b) if anchor_b is not None else None
            if anchor_b is None:
                b_tier = "n/a"
            elif k_ok:
                b_tier = "1"
            elif be is None:
                b_tier = "?"
            elif be <= anchor_b:
                b_tier = "ITM" if itm else "1B"
            else:
                b_tier = "3"
            gap = (K / anchor_b - 1) if (anchor_b and anchor_b > 0) else None
            if b_tier in ("1B", "?", "3") and not itm:
                print(f"Tier 1B test: strike {m(K)} is {p(gap)} over Floor B {m(anchor_b)} -> needs credit >= {m(hurdle, 3)}"
                      f" (have {m(credit, 3)})"
                      + (f" | PASS: premium carries the floor, cushion {m(credit - hurdle, 3)}/sh; lower tier than Tier 1"
                         f" (loss starts below BE {m(be, 3)}, the strike sits above the floor)" if b_tier == "1B" else "")
                      + (" | FAIL: BE above Floor B" if b_tier == "3" else ""))
            be_ok = b_tier in ("1", "1B", "ITM")
            g += [("BE<=Floor B (A2+SOTP)", OK if be_ok else (UNK if b_tier == "?" else NO), f"{m(be, 3)} vs {m(anchor_b)}")]
            if b_tier in ("1B", "ITM", "?"):
                g.append(("K<=Floor B", WARN if b_tier == "1B" else (UNK if b_tier == "?" else NO),
                          f"{m(K)} vs {m(anchor_b)} (+{(gap or 0) * 100:.0f}%"
                          + {"1B": ": Tier 1B)", "ITM": ": ITM -> synthetic long, not a harvest)",
                             "?": f": Tier 1B only at a fill >= {m(hurdle, 3)})"}[b_tier]))
            g += [("K<=A2 cash-only", OK if (a2 is not None and K <= a2) else WARN,
                   f"{m(K)} vs {m(a2)}{'' if (a2 is None or K <= a2) else (' - above cash floor, leans on SOTP' if resid_ps > 0 else ' - above cash floor')}"),
                  ("EV>0", OK if (ev is not None and ev > 0) else (UNK if ev is None else NO),
                   m(ev * 100 if ev is not None else None, 0))]
            tier_ok_name = "APPROVED: TIER 1 FORTRESS PUT" if b_tier == "1" \
                else ("APPROVED: TIER 1B BE-ANCHORED PUT (lower tier)"
                      + (f" only at a fill >= {m(hurdle, 3)}" if b_tier == "?" else ""))
        else:
            tier_ok_name = None
            g.append(("Catalyst window", UNK, "needed to pick Mode A vs B"))
        # Playbook Rule 1: for biotech the IV gate is a warning only (the floors carry the trade)
        g += [("IVR>=50", OK if (ivr is not None and ivr >= 50) else (UNK if ivr is None else WARN),
               m(ivr, 1) + ("" if (ivr is None or ivr >= 50) else " (Rule 1: biotech warning only)")),
              ("Mgmt", NO if mg == "RED" else (WARN if mg == "YELLOW" else (OK if mg == "GREEN" else UNK)), mg)]
        if x.get("reverse_split_pending"):
            g.append(("Reverse split", NO, "pending -> disqualified"))
        gates += g
        if tier_ok_name is None:
            verdict_put = "INCOMPLETE: map the catalyst window first (Mode A vs B)"
        elif mode.startswith("B") and b_tier == "3":
            verdict_put = "HARD REJECTION: TIER 3 SPECULATION (break-even above Floor B = A2 + SOTP)"
        elif mode.startswith("B") and b_tier == "ITM":
            verdict_put = f"NO SHORT PUT: ITM strike above Floor B = synthetic long at BE {m(be, 3)}, not a premium harvest"
        elif tier_ok_name and all(s in (OK, WARN) for _, s, _ in g):
            verdict_put = ("CONDITIONAL: " + tier_ok_name + " - confirm IV gate on IBKR IVP (52w and 26w)") if near else tier_ok_name
        elif tier_ok_name and not any(s == NO for _, s, _ in g):
            verdict_put = "CONDITIONAL: " + tier_ok_name + " - resolve UNVERIFIED gates"
        else:
            verdict_put = "NO SHORT PUT (failed: " + ", ".join(n for n, s, _ in g if s == NO) + ")"
        exp_lines, exp_cap = exposure(x, S, K, default_cls="BIO")
        for ln in exp_lines:
            print(ln)
        if exp_cap and verdict_put and verdict_put.startswith(("APPROVED", "CONDITIONAL")):
            verdict_put = ("CONDITIONAL: " + verdict_put if verdict_put.startswith("APPROVED") else verdict_put) \
                + f" - EXPOSURE: {exp_cap}"
        if caps and verdict_put and verdict_put.startswith(("APPROVED", "CONDITIONAL")):
            verdict_put = ("CONDITIONAL: " + verdict_put if verdict_put.startswith("APPROVED") else verdict_put) \
                + " - " + "; ".join(caps)
        if credit is not None:
            ivx = "IVR n/a" if ivr is None else f"IVR <= {m(ivr - 20, 0)} (consider) / <= {m(ivr - 30, 0)} (take)"
            print(f"Manage: GTC BTC @ {m(credit * 0.5, 2)} | IV-deflation exit: {ivx} | "
                  f"48h escape hatch before any ad-hoc data | Class B: no debit rolls")
    elif sh is None:
        cands = [anchor_b] if mode.startswith("B") else [raw_ps, (S * (1 - min_otm)) if S else None]
        cands = [v for v in cands if v is not None]
        max_k = min(cands) if cands else None
        print(f"Max eligible put strike: {m(max_k)} ({'Floor B = A2+SOTP' if mode.startswith('B') else 'Mode A: raw cash/sh and OTM cushion'})"
              f" -> any listed strike <= this qualifies (liquidity not gated)")
        if mode.startswith("B") and anchor_b is not None:
            ls = sorted({v for v in (f(k) for k in (x.get("listed_strikes") or [])) if v is not None})
            above = [k for k in ls if k > anchor_b and (S is None or k <= S)]
            print("Tier 1B (lower tier): an OTM strike above Floor B also qualifies if the fill >= K - Floor B"
                  + (" | hurdles: " + ", ".join(f"{k:g}P needs >= {m(k - anchor_b, 3)}" for k in above) if above else
                     " | pass listed_strikes to print the hurdle per strike"))

    # Mode C
    run = ratio(x.get("runup"))
    verdict_c = None
    if run is not None or x.get("debit_spread"):
        mult = S / a2 if (S and a2) else None
        capr = mult is not None and mult < 1.5
        c_g = [("Run-up>=50%", OK if (run is not None and run >= 0.5) else NO, p(run)),
               ("Spot>=3x A2", OK if (mult is not None and mult >= 3) else NO, f"{m(mult, 1)}x"),
               ("PoS<=30%", OK if (pos is not None and pos <= 0.30) else (UNK if pos is None else NO), p(pos))]
        vehicle = "NAKED LONG PUT allowed (IVR<40, no M&A overhang)" if (ivr is not None and ivr < 40) \
            else "BEAR PUT DEBIT SPREAD only (IVR>=40)"
        print(f"Mode C: {' | '.join(f'{n} {mark(s)} {t}' for n, s, t in c_g)}"
              f"{' | CAPR TRAP: priced for failure - NEVER short' if capr else ''} -> vehicle: {vehicle}")
        ds = x.get("debit_spread")
        if ds:
            L, Sx = leg(ds.get("long")), leg(ds.get("short"))
            lf, sf = buy_fill(L)[0], sell_fill(Sx)[0]
            # an unquoted leg or a non-positive debit is not a priced structure: no gain, no EV, no approval
            debit = (lf - sf) if (lf is not None and sf is not None) else None
            if debit is not None and debit <= 0:
                debit = None
            wid = (L["K"] or 0) - (Sx["K"] or 0)
            gain = (wid - debit) if debit is not None else None
            rr = gain / debit if debit is not None else None
            evc = ((1 - pos) * gain - pos * debit) if (pos is not None and debit is not None) else None
            if debit is None:
                print("Debit spread UNPRICED: a leg has no quote (or debit <= 0) -> pass bid/ask (or mid) for both legs")
            print(f"Debit spread {m(L['K'])}/{m(Sx['K'])}P: debit {m(debit, 3)} | max gain {m(gain, 3)} | R:R "
                  f"{m(rr, 1)}:1{'' if rr is None else (' ok' if rr >= 3 else ' below 3:1 standard')} | BE "
                  f"{m((L['K'] or 0) - debit if debit is not None else None)} | EV/ct {m(evc * 100 if evc is not None else None, 0)}"
                  f"{'' if Sx['K'] is None or a2 is None else f' | short strike vs A2 {m(a2)}'}")
            c_g.append(("EV>0", OK if (evc is not None and evc > 0) else (UNK if evc is None else NO),
                        m(evc * 100 if evc is not None else None, 0)))
        if capr:
            verdict_c = "MODE C BLOCKED: Anti-CAPR (priced for failure)"
        elif all(s == OK for _, s, _ in c_g):
            verdict_c = "APPROVED: MODE C " + ("BEAR PUT DEBIT SPREAD" if "SPREAD" in vehicle else "LONG PUT / SPREAD")
            if caps:
                verdict_c = "CONDITIONAL: " + verdict_c + " - " + "; ".join(caps)
        else:
            verdict_c = "MODE C NOT MET (" + ", ".join(n for n, s, _ in c_g if s != OK) + ")"

    # DCF + scenarios
    dcf = x.get("dcf")
    pv = pv_ps = ra_ps = None
    if dcf and fd:
        pts = (f(dcf.get("patients")) or 0) * (prob(dcf.get("biomarker")) or 1) * (prob(dcf.get("line_share")) or 1)
        netp = (f(dcf.get("list_price")) or 0) * (1 - (prob(dcf.get("gtn")) or 0.35))
        peak = pts * (prob(dcf.get("penetration")) or 0.20) * netp
        pv = peak * (f(dcf.get("multiple")) or 2.5) / (1 + (prob(dcf.get("wacc")) or 0.13)) ** (f(dcf.get("years")) or 6)
        pv_ps = pv / fd
        ra_ps = pv * loa / fd if loa is not None else None
        ev_mkt = S * fd + debt - gross if S else None
        pfp = ev_mkt is not None and ev_mkt > pv
        print(f"Napkin DCF: patients {pts:,.0f} | net price {big(netp)} | peak {big(peak)} | unrisked PV {big(pv)} "
              f"({m(pv_ps)}/sh) | risk-adj {m(ra_ps)}/sh "
              f"{'(x LoA ' + p(loa) + ')' if loa is not None else '(needs pos_loa: the event PoS is not the LoA)'}"
              f" | market EV {big(ev_mkt)}"
              f"{' -> PRICED FOR PERFECTION: Mode B disqualified' if pfp else ''}")
        if loa is None:
            missing.append("pos_loa or pos_loa_after (lead's cumulative approval odds, for the DCF)")
        # hard rule: market EV above the lead's unrisked PV disqualifies Mode B, whatever the floor says
        if pfp and mode.startswith("B") and (verdict_put or "").startswith(("APPROVED", "CONDITIONAL")):
            verdict_put = ("NO SHORT PUT: PRICED FOR PERFECTION (market EV " + big(ev_mkt)
                           + " > unrisked lead PV " + big(pv) + ") - Mode B disqualified")
    # Base/Bull carry the same SOTP as Bear. The lead's DCF replaces its Ph3-rung floor credit (no double count).
    bear = anchor_b
    sotp_ex = resid - resid_lead
    base_t = bull_t = None
    if fd and pv is not None:
        bull_t = max(0.0, (net_liq + sotp_ex + pv) / fd)
        if loa is not None:
            base_t = max(0.0, (net_liq + sotp_ex + pv * loa) / fd)
    if bull_t is not None:
        base_s = m(base_t) if base_t is not None else "n/a (needs pos_loa)"
        bull_s = m(bull_t)
        print(f"Target build (per sh): net cash {m(net_liq / fd)} + SOTP ex-lead {m(sotp_ex / fd)} + lead DCF x LoA "
              f"{m(ra_ps)} = Base | + unrisked lead DCF {m(pv_ps)} = Bull (Bear = Floor B)")
    elif mode == "A":
        base_s, bull_s = f"status quo ~{m(S)}", "n/m (Mode A: no binary inside the contract)"
    else:
        base_s = bull_s = "n/a (needs napkin DCF + pos_loa)"
    print(f"Targets: Bear {m(bear)} | Base {base_s} | Bull {bull_s}")
    if base_t is not None and bear is not None and base_t < bear - 0.005:
        print(f"\u26a0\ufe0f Base {m(base_t)} < Bear {m(bear)}: lead DCF x LoA {m(ra_ps)}/sh is below the lead's Ph3-rung "
              f"floor credit {m(resid_lead / fd)}/sh - check the DCF inputs before using Base")

    if gates:
        print("GATES: " + " | ".join(f"{n} {mark(s)} {t}" for n, s, t in gates))
    if missing:
        print("MISSING (load-bearing): " + ", ".join(missing))
    if verdict_put is None and verdict_c is None and sh is None:
        final = "FLOORS ONLY: pass short {strike, fill} to check a trade, or runup for Mode C" \
            + (" | \u26a0\ufe0f PROVISIONAL: " + "; ".join(caps) if caps else "")
    elif verdict_put and verdict_put.startswith("INCOMPLETE") and not (verdict_c or "").startswith(("APPROVED", "CONDITIONAL")):
        final = verdict_put
    elif verdict_put and verdict_put.startswith(("APPROVED", "CONDITIONAL")):
        final = "SELL PUT - " + verdict_put
    elif verdict_c and verdict_c.startswith(("APPROVED", "CONDITIONAL")):
        final = verdict_c
    else:
        final = "DO NOTHING / CASH" + (f" - {verdict_put}" if verdict_put else "") + (f" - {verdict_c}" if verdict_c else "")
    print("VERDICT: " + final)
    trading = (sh is not None and (verdict_put or "").startswith(("APPROVED", "CONDITIONAL"))) or \
              (bool(x.get("debit_spread")) and (verdict_c or "").startswith(("APPROVED", "CONDITIONAL")))
    escalate([
        "load-bearing data UNVERIFIED: " + ", ".join(missing) if missing else None,
        "debt acceleration trap / negative net cash - SOTP judgment sets the floor" if (trap or netted) else None,
        "Mode B binary with no PoS estimate - needs trial-design judgment" if (mode.startswith("B") and pos is None) else None,
        "management flagged YELLOW/RED - judgment call on guidance credibility" if (mode.startswith("B") and mg in ("YELLOW", "RED")) else None,
        "IV gate resting on an unconfirmed proxy" if near else None,
        "Tier 1B: premium carries the floor, not the strike - confirm before sizing" if b_tier == "1B" else None,
        "sizing real capital - final check before the order" if trading else None,
    ])


# ---------- assigned / underwater lot re-underwrite ----------
def call_delta(S, K, T, r, q, sig):
    pdl = put_delta(S, K, T, r, q, sig)
    return None if pdl is None else pdl + math.exp(-q * T)


def call_strike_for_delta(S, T, r, q, sig, target):
    lo, hi = S, 5 * S
    for _ in range(80):
        mid = (lo + hi) / 2
        if call_delta(S, mid, T, r, q, sig) > target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def lot(x):
    """Re-underwrite a held (often assigned) stock lot as if it were a fresh entry today."""
    T_ = x.get("ticker", "?")
    S, sh, avg = f(x.get("spot")), f(x.get("shares")), f(x.get("avg_cost"))
    nav = f(x.get("nav"))
    mcap = f(x.get("mcap"))
    ocf, capex, sbc = f(x.get("ocf_ttm")), f(x.get("capex_ttm")), f(x.get("sbc_ttm"))
    cash, debt = f(x.get("cash")), f(x.get("debt"))
    iv, dte = vol(x.get("iv")), f(x.get("dte")) or 38
    r, q = f(x.get("r")) or 0.047, yld(x.get("div_yield")) or 0.0
    if None in (S, sh, avg):
        print("need ticker, spot, shares, avg_cost")
        return
    upl = sh * (S - avg)
    dd = S / avg - 1
    cls, thr = rule7(x.get("class"), "LC")  # universe.md class sets the Rule 7 no-new-puts line
    mv = sh * S
    print(f"{T_} lot: {sh:,.0f} sh @ {m(avg)} | spot {m(S)} | MV {big(mv)} ({p(mv / nav if nav else None)} of NAV)"
          f" | unrealized {big(upl)} ({p(dd)})")
    fcf = (ocf - capex) if (ocf is not None and capex is not None) else None
    owner = (fcf - sbc) if (fcf is not None and sbc is not None) else None
    dev = debt / (mcap + debt - (cash or 0)) if (debt is not None and mcap) else None
    fails = []
    if mcap is not None and mcap < 5e9:
        fails.append("mcap < $5B")
    if owner is not None and owner <= 0:
        fails.append("owner FCF <= 0")
    if dev is not None and dev > 0.50:
        fails.append(f"D/EV {p(dev)} > 50%")
    if x.get("structural_impairment"):
        fails.append("structural impairment (thesis broken)")
    unknown = owner is None or mcap is None
    print(f"Re-underwrite: owner FCF {big(owner)} | D/EV {p(dev)} | mcap {big(mcap)} -> "
          f"{'FAIL: ' + ', '.join(fails) if fails else ('UNVERIFIED' if unknown else 'PASS')}")
    if iv:
        T = dte / 365.0
        k30 = call_strike_for_delta(S, T, r, q, iv, 0.30)
        d_basis = call_delta(S, avg, T, r, q, iv) if avg > S else None
        print(f"Covered call ({int(dte)} DTE, IV {p(iv)}): d0.30 strike ~{m(k30)} | cost basis {m(avg)}"
              f"{'' if d_basis is None else f' -> call at basis is d{d_basis:.2f}'}"
              f"{' | WARNING: d0.30 strike < basis: assignment realizes the loss' if k30 < avg else ''}")
    if fails:
        v = "EXIT OR HEDGE (collar / sell): would not pass as a fresh entry today"
    elif unknown:
        v = "INCOMPLETE: pull forensics (OCF, CapEx, SBC, cash, debt, mcap) before deciding"
    elif dd <= -0.25:
        v = (f"KEEP ONLY WITH A PLAN: passes re-underwrite but >25% under cost -> wheel calls at/above basis if premium "
             f"allows, NO new puts on this name until within {p(thr, 0)} of cost ({cls}, Rule 7); written plan within 1 week")
    elif dd <= -thr:
        v = f"KEEP - WHEEL: sell calls at/above basis; no new puts on this name until within {p(thr, 0)} of cost ({cls}, Rule 7)"
    else:
        v = "KEEP - WHEEL: normal covered-call management"
    print("VERDICT: " + v)


if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] not in ("lc", "bio", "strikes", "lot"):
        print(__doc__)
        sys.exit(1)
    {"lc": lc, "bio": bio, "strikes": strikes, "lot": lot}[sys.argv[1]](load(sys.argv[2]))
