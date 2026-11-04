#!/usr/bin/env python3
"""
valuation.py - deterministic valuation calculator for the stock-valuation-engine (VALU) skill.
Feeds the large-cap-put-overreaction (LC) skill through the VALU_HANDOFF line (val_floor).
Stdlib only. Missing inputs print 'n/a' or UNVERIFIED; the script never crashes on gaps.

  python3 valuation.py valu '<json>'     # inline JSON, a file path, or '-' for stdin

Units: statement money in $ MILLIONS (Zacks native; divide SEC raw dollars by 1e6). shares in MILLIONS.
spot / EPS / prices per share. Rates as decimals (0.045) or % (4.5). Peer pe/ps/peg as printed;
peer chg4w / chg12w and est_rev_4wk in percent points (-5.3 = -5.3%), as Zacks prints them.
Growth overrides g.bear/base/bull as decimals (0.08).
Zacks quarterly cash flow is YEAR-TO-DATE: pass it as returned with cf_mode "ytd" (default) plus fy_end.
cf_q rows take an optional "da" (D&A, same YTD basis): the maintenance-capex proxy for the capex-adjusted read.
Peers take an optional "pe_f2": used instead of pe_f1 when GAAP EPS is flagged as distorted.
"""
import json
import sys
from datetime import date, datetime

GT = 0.025  # terminal growth


# ---------- helpers ----------
def f(v):
    try:
        return None if v is None or v == "" else float(v)
    except (TypeError, ValueError):
        return None


def rate(v):
    v = f(v)
    return None if v is None else (v / 100.0 if abs(v) > 1 else v)


def d(s):
    if not s:
        return None
    try:
        return datetime.strptime(str(s)[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def m(x, dp=2):
    return "n/a" if x is None else f"{x:,.{dp}f}"


def p(x, dp=1):
    return "n/a" if x is None else f"{x * 100:+.{dp}f}%"


def pa(x, dp=1):
    return "n/a" if x is None else f"{x * 100:.{dp}f}%"


def bigm(x):
    """$ millions -> readable."""
    if x is None:
        return "n/a"
    a, sg = abs(x), ("-" if x < 0 else "")
    return f"{sg}${a / 1e3:,.2f}B" if a >= 1e3 else f"{sg}${a:,.0f}M"


def median(xs):
    xs = sorted(v for v in xs if v is not None)
    if not xs:
        return None
    n = len(xs)
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2


def months(a, b):
    """Whole months from date a to date b."""
    return (b.year * 12 + b.month) - (a.year * 12 + a.month)


def load(arg):
    if arg == "-":
        return json.load(sys.stdin)
    if arg.strip().startswith("{"):
        return json.loads(arg)
    with open(arg) as fh:
        return json.load(fh)


# ---------- cash flow: YTD -> discrete quarters and TTM ----------
def fiscal_q(end, fy_end):
    """1..4 fiscal quarter of a period end (4 = fiscal year end). Rounds to the nearest quarter,
    so 52/53-week calendars (Sep 27, Jan 1) still map correctly."""
    if not end or not fy_end:
        return None
    q = int(round((months(fy_end, end) % 12) / 3.0)) % 4
    return 4 if q == 0 else q


def cf_series(rows, fy_end, mode):
    """rows: [{end, ocf, capex, da?}] any order. da = depreciation & amortization (optional, same basis as ocf).
    Returns (ttm dict {ocf, capex, da}, quarters newest-first, note). A TTM value is None when it can't be built."""
    K = ("ocf", "capex", "da")
    recs = []
    for r in rows or []:
        e = d(r.get("end"))
        if e:
            cx = f(r.get("capex"))
            recs.append({"end": e, "ocf": f(r.get("ocf")), "capex": abs(cx) if cx is not None else 0.0,
                         "da": f(r.get("da"))})
    recs.sort(key=lambda r: r["end"], reverse=True)
    none = {k: None for k in K}
    if not recs:
        return none, [], "no cash-flow rows"

    def tot(rs, k):
        return sum(r[k] for r in rs) if rs and all(r[k] is not None for r in rs) else None

    if mode == "discrete":
        qs = recs[:4]
        if len(qs) < 4 or any(r["ocf"] is None for r in qs):
            return none, qs, "fewer than 4 discrete quarters"
        return {k: tot(qs, k) for k in K}, qs, "discrete quarters summed"
    if not fy_end:
        return none, [], "cf_mode ytd needs fy_end (Zacks lst_com_fy)"
    for r in recs:
        r["fq"] = fiscal_q(r["end"], fy_end)
    sub = lambda a, b: (a - b) if (a is not None and b is not None) else None
    add3 = lambda a, b, c: (a + b - c) if None not in (a, b, c) else None
    # discrete quarters: Q1 = YTD; otherwise YTD minus the previous quarter's YTD (3 months earlier)
    qs = []
    for i, r in enumerate(recs):
        if r["ocf"] is None:
            continue
        if r["fq"] == 1:
            qs.append({"end": r["end"], **{k: r[k] for k in K}})
        elif i + 1 < len(recs) and recs[i + 1]["ocf"] is not None and abs(months(recs[i + 1]["end"], r["end"]) - 3) <= 1:
            o = recs[i + 1]
            qs.append({"end": r["end"], **{k: sub(r[k], o[k]) for k in K}})
    L = recs[0]
    if L["ocf"] is None:
        return none, qs, "latest cash-flow row empty"
    if L["fq"] == 4:
        return {k: L[k] for k in K}, qs, f"latest row is fiscal year {L['end']}"
    fy = next((r for r in recs[1:] if r["fq"] == 4 and r["ocf"] is not None), None)
    prior = next((r for r in recs[1:] if abs(months(r["end"], L["end"]) - 12) <= 1 and r["ocf"] is not None), None)
    if fy and prior:
        return ({k: add3(L[k], fy[k], prior[k]) for k in K}, qs,
                f"TTM = YTD {L['end']} + FY {fy['end']} - prior YTD {prior['end']}")
    if len(qs) >= 4:
        q4 = qs[:4]
        return {k: tot(q4, k) for k in K}, qs, "TTM = last 4 de-cumulated quarters"
    return none, qs, "not enough YTD rows for TTM (pass 5 quarterly rows)"


# ---------- DCF ----------
def dcf_ev(fcf0, g, r, gt=GT, years=10, stage1=5):
    """Owner FCF grows at g for `stage1` years, fades linearly to gt by year `years`, then Gordon terminal."""
    if fcf0 is None or g is None or r is None or r <= gt:
        return None
    pv, cf = 0.0, fcf0
    for t in range(1, years + 1):
        gr = g if t <= stage1 else g + (gt - g) * (t - stage1) / float(years - stage1)
        cf *= (1 + gr)
        pv += cf / (1 + r) ** t
    return pv + cf * (1 + gt) / (r - gt) / (1 + r) ** years


def implied_g(fcf0, ev, r):
    """Stage-1 growth that makes the DCF equal today's EV (reverse DCF)."""
    if not fcf0 or fcf0 <= 0 or ev is None or ev <= 0 or r is None or r <= GT:
        return None
    lo, hi = -0.50, 1.00
    if dcf_ev(fcf0, hi, r) < ev:
        return hi  # implies > 100%/yr: pegged at the cap
    if dcf_ev(fcf0, lo, r) > ev:
        return lo
    for _ in range(80):
        mid = (lo + hi) / 2
        if dcf_ev(fcf0, mid, r) < ev:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


# ---------- main ----------
def valu(x):
    T_ = x.get("ticker", "?")
    asof = d(x.get("asof")) or date.today()
    S = f(x.get("spot"))
    fy_end = d(x.get("fy_end"))
    shares = f(x.get("shares"))
    mcap = f(x.get("mcap"))
    if shares is None and mcap and (f(x.get("mcap_px")) or S):
        shares = mcap / (f(x.get("mcap_px")) or S)
    if S and shares:
        mcap = S * shares  # re-mark to the live spot
    cash, debt, sbc = f(x.get("cash")), f(x.get("debt")), f(x.get("sbc_ttm"))
    fin = bool(x.get("financial"))
    unver = []
    print(f"{T_} | asof {asof} | spot {m(S)} | mcap {bigm(mcap)} | shares {m(shares, 1)}M | cash {bigm(cash)} debt {bigm(debt)}")
    if S is None:
        unver.append("spot")
    if shares is None:
        unver.append("shares/mcap")

    # ---- 1. last 4 earnings ----
    # GAAP distortion: net income far from its normal ratio to operating income means non-operating items
    # (equity-stake marks, one-off gains/losses) are swinging GAAP EPS. Normal ratio = median NI/op income of
    # the quarters passed, clamped to 0.6-1.0; a quarter more than 25% off it is flagged.
    isq_all = sorted((r for r in (x.get("is_q") or []) if d(r.get("end"))), key=lambda r: d(r["end"]))
    ratios = [f(r.get("ni")) / f(r.get("op_inc")) for r in isq_all
              if f(r.get("ni")) is not None and (f(r.get("op_inc")) or 0) > 0]
    ref = min(1.0, max(0.6, median(ratios))) if ratios else None

    def distorted(r):
        ni, op = f(r.get("ni")), f(r.get("op_inc"))
        if ref is None or ni is None or not op or op <= 0:
            return False
        return abs(ni / op / ref - 1) > 0.25

    isq4 = isq_all[-4:]
    dist4 = [distorted(r) for r in isq4]
    sur = [s for s in (x.get("surprises") or []) if f(s.get("act")) is not None and f(s.get("est")) is not None][-4:]
    beats = sum(1 for s in sur if f(s["act"]) >= f(s["est"]))
    srel = lambda s: (f(s["act"]) - f(s["est"])) / abs(f(s["est"])) if f(s["est"]) else None
    avg_sur = None if not sur else (sum(srel(s) for s in sur if srel(s) is not None) / len(sur))
    # surprises and is_q are both oldest->newest; align them on the latest quarter
    sur_flag = [dist4[len(dist4) - len(sur) + i] if len(dist4) >= len(sur) else False for i in range(len(sur))]
    clean = [srel(s) for s, fl in zip(sur, sur_flag) if not fl and srel(s) is not None]
    avg_sur_clean = (sum(clean) / len(clean)) if clean else None
    sales_q = [f(v) for v in (x.get("sales_q") or [])]
    revs = [f(r.get("rev")) for r in sorted((r for r in (x.get("is_q") or []) if d(r.get("end"))), key=lambda r: d(r["end"]))]
    if len(revs) > len(sales_q) and None not in revs:
        sales_q = revs  # 8 discrete snapshot quarters beat Zacks' 7-actual estimate table
    eps_q = [f(v) for v in (x.get("eps_adj_q") or [])]

    def yoy(series):
        out = []
        for k in range(4, 0, -1):  # oldest of the last 4 first
            i = len(series) - k
            if i - 4 >= 0 and series[i] is not None and series[i - 4]:
                out.append(series[i] / series[i - 4] - 1)
            else:
                out.append(None)
        return out

    s_yoy, e_yoy = yoy(sales_q), yoy(eps_q)
    sales_ttm = sum(sales_q[-4:]) if len(sales_q) >= 4 and None not in sales_q[-4:] else None
    sales_prev = sum(sales_q[-8:-4]) if len(sales_q) >= 8 and None not in sales_q[-8:-4] else None
    ttm_sales_g = (sales_ttm / sales_prev - 1) if (sales_ttm and sales_prev) else None
    trend = "n/a"
    known = [v for v in s_yoy if v is not None]
    if len(known) >= 2:
        dlt = known[-1] - known[0]
        trend = ("SHRINKING" if known[-1] < 0 else
                 "ACCELERATING" if dlt > 0.02 else "DECELERATING" if dlt < -0.02 else "STEADY")
    isq = isq4
    ni_ttm = sum(f(r.get("ni")) for r in isq) if len(isq) == 4 and all(f(r.get("ni")) is not None for r in isq) else None
    op_ttm = sum(f(r.get("op_inc")) for r in isq) if len(isq) == 4 and all(f(r.get("op_inc")) is not None for r in isq) else None
    eps_gaap_ttm = sum(f(r.get("eps")) for r in isq) if len(isq) == 4 and all(f(r.get("eps")) is not None for r in isq) else None
    eps_adj_ttm = sum(eps_q[-4:]) if len(eps_q) >= 4 and None not in eps_q[-4:] else None
    margins = [f(r.get("op_inc")) / f(r.get("rev")) for r in isq if f(r.get("op_inc")) is not None and f(r.get("rev"))]
    ttm_ratio = (ni_ttm / op_ttm) if (ni_ttm is not None and op_ttm and op_ttm > 0) else None
    eps_distorted = bool((ttm_ratio is not None and ref and abs(ttm_ratio / ref - 1) > 0.25) or sum(dist4) >= 2)
    flagged = [str(d(r["end"])) for r, fl in zip(isq4, dist4) if fl]
    print(f"Earnings (last {len(sur)}): beats {beats}/{len(sur)} | avg EPS surprise {p(avg_sur)}"
          + (f" (ex GAAP-distorted quarters {p(avg_sur_clean)}, {len(clean)} left)" if any(sur_flag) else "")
          + f" | sales YoY {' / '.join(p(v, 0) for v in s_yoy)} -> {trend} | adj EPS YoY {' / '.join(p(v, 0) for v in e_yoy)} | "
          f"op margin {' / '.join(pa(v, 0) for v in margins) or 'n/a'}"
          f"{'' if f(x.get('est_rev_4wk')) is None else ' | FY EPS est 4wk ' + p(f(x.get('est_rev_4wk')) / 100)}")
    if flagged or eps_distorted:
        print(f"  GAAP distortion: NI/op income normal {m(ref)}x, TTM {m(ttm_ratio)}x | quarters flagged {', '.join(flagged) or 'none'}"
              + (" -> EPS_DISTORTED: P/E uses F2 and growth ignores F1->F2" if eps_distorted else ""))

    # ---- 2. owner cash flow ----
    ttm, qs, cf_note = cf_series(x.get("cf_q"), fy_end, x.get("cf_mode", "ytd"))
    ocf, capex, da = ttm["ocf"], ttm["capex"], ttm["da"]
    fcf = (ocf - capex) if (ocf is not None and capex is not None) else None
    owner = (fcf - sbc) if (fcf is not None and sbc is not None) else None
    if owner is None and not fin:
        unver.append("owner FCF (OCF/CapEx/SBC)")
    # growth-capex adjustment: maintenance capex proxied by D&A (never above actual capex). Only drives the
    # valuation when owner FCF after ALL capex is <= 0 (build-out phase); always an upper-bound read.
    maint = min(capex, da) if (capex is not None and da is not None and da > 0) else None
    fcf_adj = (ocf - maint) if (ocf is not None and maint is not None) else None
    owner_adj = (fcf_adj - sbc) if (fcf_adj is not None and sbc is not None) else None
    conv = owner / ni_ttm if (owner is not None and ni_ttm and ni_ttm > 0) else None
    gap = (eps_adj_ttm / eps_gaap_ttm - 1) if (eps_adj_ttm and eps_gaap_ttm and eps_gaap_ttm > 0) else None
    print(f"Owner cash: OCF {bigm(ocf)} - CapEx {bigm(capex)} - SBC {bigm(sbc)} = owner FCF {bigm(owner)} "
          f"({cf_note}) | SBC/OCF {pa(sbc / ocf if (sbc is not None and ocf) else None)} | owner FCF / GAAP NI "
          f"{m(conv)}x | adj EPS vs GAAP {p(gap, 0)}")
    if maint is not None:
        print(f"  capex-adjusted: OCF - maint capex (D&A) {bigm(maint)} - SBC = owner FCF adj {bigm(owner_adj)} | "
              f"growth capex {bigm(capex - maint)} ({pa((capex - maint) / capex if capex else None, 0)} of capex)")
    if qs:
        print("  quarters (de-cumulated, newest first): " +
              " | ".join(f"{r['end']} OCF {bigm(r['ocf'])} capex {bigm(r['capex'])}" for r in qs[:4]))
    quality = "n/a"
    if conv is not None or gap is not None or owner is not None:
        bad = (conv is not None and conv < 0.7) or (gap is not None and gap > 0.40) or \
              (sbc is not None and ocf and sbc / ocf > 0.25) or (owner is not None and owner <= 0)
        quality = "LOW (cash or GAAP gap)" if bad else "OK"

    # ---- 3. market (Zacks compare_stocks: raw and S&P-relative % changes; S&P move = (1+t)/(1+rel) - 1) ----
    pc = lambda k: (f(x.get(k)) / 100) if f(x.get(k)) is not None else None
    t4, t12, rel4, rel12 = pc("t_chg4w"), pc("t_chg12w"), pc("t_rel4w"), pc("t_rel12w")
    s4 = ((1 + t4) / (1 + rel4) - 1) if (t4 is not None and rel4 is not None) else None
    s12 = ((1 + t12) / (1 + rel12) - 1) if (t12 is not None and rel12 is not None) else None
    # Zacks moves are as of its last close; re-mark the stock's leg to the live spot (S&P backed out first, left as is)
    zpx = f(x.get("zacks_px"))
    remark = (S / zpx) if (S and zpx) else None
    if remark:
        t4 = (1 + t4) * remark - 1 if t4 is not None else None
        t12 = (1 + t12) * remark - 1 if t12 is not None else None
    beta = f(x.get("beta"))
    peers = x.get("peers") or []
    p12 = median([f(q.get("chg12w")) / 100 if f(q.get("chg12w")) is not None else None for q in peers])
    mkt_part = beta * s12 if (beta is not None and s12 is not None) else None
    resid = (t12 - mkt_part) if (t12 is not None and mkt_part is not None) else None
    idio = (t12 - p12) if (t12 is not None and p12 is not None) else None
    cls = "n/a"
    if t12 is not None:
        # relative first: a flat stock in a rising tape is still a company-specific move
        if idio is not None and abs(idio) >= 0.08:
            cls = "COMPANY-SPECIFIC (" + ("lagging" if idio < 0 else "leading") + " peers)"
        elif abs(t12) < 0.05 and (resid is None or abs(resid) < 0.05):
            cls = "NO MAJOR MOVE"
        elif resid is not None and abs(resid) < 0.05:
            cls = "MARKET-DRIVEN"
        elif p12 is not None and abs(t12) >= 0.05 and abs(p12) >= 0.05 and (t12 < 0) == (p12 < 0):
            cls = "SECTOR-WIDE"
        else:
            cls = "MIXED (" + ("behind" if (resid or 0) < 0 else "ahead of") + " the market, within 8 pts of peers)"
    print(f"Market: beta {m(beta)} | 12w: stock {p(t12)} S&P {p(s12)} peers med {p(p12)} | market-explained "
          f"{p(mkt_part)} residual {p(resid)} | vs peers {p(idio)} -> {cls} | 4w: stock {p(t4)} S&P {p(s4)}"
          + (f" | stock leg re-marked to spot ({p(remark - 1)} vs Zacks close {m(zpx)})" if remark
             else " | UNVERIFIED: moves as of the Zacks close (pass zacks_px)"))

    # ---- 4. valuation ----
    rf = rate(x.get("rf")) or 0.045
    erp = rate(x.get("erp")) or 0.05
    r = min(0.14, max(0.07, rf + (beta if beta is not None else 1.0) * erp))
    ev = (mcap + (debt or 0) - (cash or 0)) if mcap else None
    if debt is None or cash is None:
        unver.append("cash/debt")
    eq = (lambda e: (e - (debt or 0) + (cash or 0)) / shares if (e is not None and shares) else None)
    eps_f1, eps_f2 = f(x.get("eps_f1")), f(x.get("eps_f2"))
    f1f2 = (eps_f2 / eps_f1 - 1) if (eps_f1 and eps_f2 and eps_f1 > 0) else None
    cands = [v for v in (None if eps_distorted else f1f2, ttm_sales_g) if v is not None]
    gin = x.get("g") or {}
    g_base = rate(gin.get("base"))
    if g_base is None:
        g_base = max(-0.05, min(0.20, sum(cands) / len(cands))) if cands else None
    g_bear = rate(gin.get("bear"))
    g_bull = rate(gin.get("bull"))
    if g_base is not None:
        if g_bear is None:
            g_bear = g_base - max(0.05, 0.5 * abs(g_base))
        if g_bull is None:
            g_bull = min(0.30, g_base + max(0.03, 0.5 * abs(g_base)))
    dcf_ok = owner is not None and owner > 0 and not fin
    adj_on = (not dcf_ok and not fin and owner_adj is not None and owner_adj > 0)
    cf0 = owner if dcf_ok else (owner_adj if adj_on else None)
    run = dcf_ok or adj_on
    tag = "" if dcf_ok else " [CAPEX-ADJ]"
    v_bear = eq(dcf_ev(cf0, g_bear, r + 0.01)) if run else None
    v_base = eq(dcf_ev(cf0, g_base, r)) if run else None
    v_bull = eq(dcf_ev(cf0, g_bull, r - 0.005)) if run else None
    v_base_up = eq(dcf_ev(cf0, g_base, r + 0.01)) if run else None
    ig_run = implied_g(cf0, ev, r) if run else None
    ig_up = implied_g(cf0, ev, r + 0.01) if run else None
    ig = ig_run if dcf_ok else None
    ig_adj = ig_run if adj_on else None
    if not dcf_ok and not fin:
        print("DCF: owner FCF <= 0 or missing after all capex (no owner cash to discount)"
              + (" -> DCF below runs on capex-adjusted owner FCF (D&A as maintenance capex): an UPPER-BOUND read"
                 if adj_on else " and no D&A to separate growth capex (pass cf_q[].da)"))
    print(f"Rates: r = rf {pa(rf)}{'' if x.get('rf') is not None else ' (ASSUMED)'} + beta x ERP {pa(erp)} = {pa(r)} | "
          f"+100bp -> base value {p((v_base_up / v_base - 1) if (v_base and v_base_up) else None)}{tag}")
    print(f"Reverse DCF{tag}: price implies {p(ig_run)} owner-FCF growth/yr for 5y (fading to {pa(GT)}) at r {pa(r)}; "
          f"{p(ig_up)} at r +1% | inputs: EPS F1->F2 {p(f1f2)}{' (ignored: EPS_DISTORTED)' if eps_distorted else ''}, "
          f"TTM sales {p(ttm_sales_g)}")
    print(f"DCF/sh{tag}: bear {m(v_bear)} (g {p(g_bear)}, r {pa(r + 0.01)}) | base {m(v_base)} (g {p(g_base)}) | "
          f"bull {m(v_bull)} (g {p(g_bull)}, r {pa(r - 0.005)})")

    # own history: P/FCF at each fiscal year's low (current share count: buybacks make past multiples look lower -> conservative)
    pm = x.get("px_m") or {}
    bars = [(d(str(t)[:7] + "-01"), f(lo)) for t, lo in zip(pm.get("t") or [], pm.get("l") or [])]
    bars = [(t, lo) for t, lo in bars if t and lo is not None]
    hist = []
    for a in x.get("annual") or []:
        e = d(a.get("end"))
        fa = (f(a.get("ocf")) - abs(f(a.get("capex")) or 0.0)) if f(a.get("ocf")) is not None else None
        sh_y = (f(a.get("ni")) / f(a.get("eps"))) if (f(a.get("ni")) and f(a.get("eps"))) else None
        if not sh_y or sh_y <= 0:
            sh_y = shares  # loss year or no EPS: fall back to today's count
        if not e or not fa or fa <= 0 or not sh_y:
            continue
        w = [lo for t, lo in bars if 0 <= months(t, e) <= 11]  # the 12 monthly bars ending in the FY-end month
        if len(w) >= 10:
            hist.append((e, min(w) * sh_y / fa))
    trough = min((v for _, v in hist), default=None)
    hmed = median([v for _, v in hist])
    fcf_v = fcf if dcf_ok else (fcf_adj if adj_on else fcf)  # FCF the history multiple is applied to
    pfcf = mcap / fcf if (mcap and fcf and fcf > 0) else None
    powner = mcap / owner if (mcap and owner and owner > 0) else None
    v_trough = trough * cf0 / shares if (trough and cf0 and cf0 > 0 and shares) else None
    v_hmed = hmed * fcf_v / shares if (hmed and fcf_v and fcf_v > 0 and shares) else None
    print(f"Own history ({len(hist)} FY): P/FCF at yearly lows {' / '.join(f'{e.year} {v:.1f}x' for e, v in hist) or 'n/a'} | "
          f"trough {m(trough, 1)}x median {m(hmed, 1)}x | now P/FCF {m(pfcf, 1)}x P/owner-FCF {m(powner, 1)}x"
          + (f" P/owner-FCF adj {m(mcap / owner_adj, 1)}x" if (adj_on and mcap) else "")
          + f" | trough x owner FCF{tag} = {m(v_trough)}/sh | median x FCF{tag} = {m(v_hmed)}/sh")

    # peers: when GAAP EPS is distorted, F1 carries the one-offs -> value on F2 with the peers' F2 multiple
    use_f2 = eps_distorted and eps_f2 and eps_f2 > 0
    pe_key, eps_pe = ("pe_f2", eps_f2) if use_f2 else ("pe_f1", eps_f1)
    pe_list = [f(q.get(pe_key)) for q in peers if (f(q.get(pe_key)) or 0) > 0]
    if use_f2 and not pe_list:  # peers' F2 multiples not passed: fall back to their F1 multiple on our F2
        pe_key, pe_list = "pe_f1 (no pe_f2 passed)", [f(q.get("pe_f1")) for q in peers if (f(q.get("pe_f1")) or 0) > 0]
    pe_med = median(pe_list)
    ps_med = median([f(q.get("ps")) for q in peers if (f(q.get("ps")) or 0) > 0])
    peg_med = median([f(q.get("peg")) for q in peers if (f(q.get("peg")) or 0) > 0])
    v_pe = pe_med * eps_pe if (pe_med and eps_pe and eps_pe > 0) else None
    v_ps = ps_med * sales_ttm / shares if (ps_med and sales_ttm and shares) else None
    t_pe = S / eps_pe if (S and eps_pe and eps_pe > 0) else None
    t_ps = mcap / sales_ttm if (mcap and sales_ttm) else None
    basis = "F2" if use_f2 else "F1"
    print(f"Peers ({', '.join(str(q.get('t')) for q in peers) or 'none'}): fwd P/E ({basis} EPS {m(eps_pe)}, peer {pe_key}) "
          f"med {m(pe_med, 1)}x vs {m(t_pe, 1)}x ({p((t_pe / pe_med - 1) if (t_pe and pe_med) else None, 0)}) | "
          f"P/S med {m(ps_med, 1)}x vs {m(t_ps, 1)}x | PEG med {m(peg_med)} vs {m(f(x.get('peg')))} | "
          f"implied/sh: fwd P/E {m(v_pe)} | P/S {m(v_ps)}")
    if not peers:
        unver.append("peers")

    # ---- verdict ----
    def grade(fl, fr):
        if fl is not None and abs(S / fl - 1) <= 0.02:
            return f"AT FLOOR: spot within 2% of the floor ({p(S / fl - 1)}) - no cushion"
        if fl is not None and S < fl:
            return f"DEEP VALUE: spot {p(S / fl - 1)} below the floor"
        return "UNDERVALUED" if S < fr * 0.85 else "FAIRLY VALUED" if S <= fr * 1.15 else "RICH"

    floor = min([v for v in (v_bear, v_trough) if v is not None], default=None) if dcf_ok else None
    floor_adj = min([v for v in (v_bear, v_trough) if v is not None], default=None) if adj_on else None
    fair_adj = median([v_base, v_hmed, v_pe]) if adj_on else None
    if dcf_ok:
        fair, parts = median([v_base, v_hmed, v_pe]), f"median of base DCF {m(v_base)}, history {m(v_hmed)}, peer P/E {m(v_pe)}"
    elif fin:
        fair, parts = v_pe, f"peer P/E {m(v_pe)} (financial: P/E only)"
    else:  # no owner cash after all capex: only market comparables left
        fair, parts = median([v_pe, v_ps]), f"median of peer P/E ({basis}) {m(v_pe)}, peer P/S {m(v_ps)}"
    mos = (fair / S - 1) if (fair and S) else None
    mos_adj = (fair_adj / S - 1) if (fair_adj and S) else None
    if fair is None or S is None:
        v = "INCOMPLETE: fair value needs owner FCF, peers or estimates"
    elif not dcf_ok and not fin:
        v = "SPECULATIVE: no owner cash flow after all capex - headline fair rests on peer multiples only"
        if adj_on and fair_adj:
            v += f"; capex-adjusted read {grade(floor_adj, fair_adj).split(':')[0]}"
    elif fin:
        v = grade(None, fair)
    else:
        v = grade(floor, fair)
    print(f"Range/sh: floor {m(floor)} | fair {m(fair)} | bull {m(v_bull if dcf_ok else None)} | spot {m(S)} -> "
          f"margin of safety {p(mos)} | earnings {trend}, quality {quality}, move {cls}")
    print(f"  fair = {parts}")
    if adj_on:
        print(f"Capex-adjusted range/sh (UPPER BOUND, D&A as maintenance capex): floor {m(floor_adj)} | fair {m(fair_adj)} "
              f"(median of base DCF {m(v_base)}, history {m(v_hmed)}, peer P/E {m(v_pe)}) | bull {m(v_bull)} | "
              f"margin of safety {p(mos_adj)} | implied growth {p(ig_adj)}")
    if unver:
        print("UNVERIFIED: " + ", ".join(unver))
    print("VERDICT: " + v)
    rnd = lambda v_, k=2: None if v_ is None else round(v_, k)
    hand = {"ticker": T_, "asof": str(asof), "val_floor": rnd(floor), "val_fair": rnd(fair), "val_implied_g": rnd(ig, 4),
            "val_r": round(r, 4), "val_trough_pfcf": rnd(trough, 1),
            "val_move": cls, "val_trend": trend, "val_verdict": v.split(":")[0]}
    if adj_on:
        hand.update({"val_floor_adj": rnd(floor_adj), "val_fair_adj": rnd(fair_adj), "val_implied_g_adj": rnd(ig_adj, 4)})
    if eps_distorted:
        hand["val_eps_basis"] = basis
    print("VALU_HANDOFF " + json.dumps(hand))


if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] != "valu":
        print(__doc__)
        sys.exit(1)
    valu(load(sys.argv[2]))
