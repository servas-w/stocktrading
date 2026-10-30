#!/usr/bin/env python3
"""
valuation.py - deterministic valuation calculator for the stock-valuation-engine (VALU) skill,
Gemini Spark edition (same math as the Claude version; inputs come from public web pages).
Stdlib only, no network. Missing inputs print 'n/a' or UNVERIFIED; the script never crashes on gaps.

  python3 valuation.py valu '<json>'     # inline JSON, a file path, or '-' for stdin
  or: import valuation; valuation.valu({...})

Units: statement money in $ MILLIONS. shares in MILLIONS. spot / EPS / prices per share.
Rates as decimals (0.045) or % (4.5). Peer pe/ps/peg as printed; peer chg4w / chg12w, the stock's
t_chg4w / t_chg12w, the S&P's s_chg4w / s_chg12w and est_rev_4wk in percent points (-5.3 = -5.3%).
Growth overrides g.bear/base/bull as decimals (0.08).
Cash flow: stockanalysis.com quarterly figures are DISCRETE quarters -> cf_mode "discrete" (4+ rows).
Year-to-date figures (10-Q style) -> cf_mode "ytd" plus fy_end.
"""
import json
import sys
from datetime import date, datetime

GT = 0.025  # terminal growth


# ---------- helpers ----------
WARN = []  # input problems found this run; printed before the verdict
_SCALE = {"K": 1e-3, "M": 1.0, "B": 1e3, "T": 1e6}  # suffixes scale to MILLIONS (money and shares)
_MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}


def f(v):
    """Number as web pages print it: 10,031 · (85) · $268.54 · 389.20M · 1.2B · -3.18% · −0.5 · n/a."""
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    t = str(v).strip().replace(",", "").replace("$", "").replace("%", "").replace("\u2212", "-").replace(" ", "")
    if t in ("", "-", "--", "n/a", "N/A", "NA", "None", "null"):
        return None
    neg = t.startswith("(") and t.endswith(")")
    t = t.strip("()")
    scale = 1.0
    if t and t[-1].upper() in _SCALE:
        scale, t = _SCALE[t[-1].upper()], t[:-1]
    try:
        x = float(t) * scale
    except ValueError:
        return None
    return -x if neg else x


def rate(v):
    v = f(v)
    return None if v is None else (v / 100.0 if abs(v) > 1 else v)


def d(s):
    """Date as pages print it: 2026-08-31 · 2026-08 · Aug 31, 2026 · August 31 2026 · 8/31/2026 · Aug 2026."""
    if not s:
        return None
    if isinstance(s, date):
        return s
    t = str(s).strip()
    for fmt, n in (("%Y-%m-%d", 10), ("%m/%d/%Y", None), ("%Y-%m", 7)):
        try:
            return datetime.strptime(t if n is None else t[:n], fmt).date()
        except ValueError:
            pass
    parts = t.replace(",", " ").split()
    if parts and parts[0][:3].lower() in _MONTHS:
        mo = _MONTHS[parts[0][:3].lower()]
        nums = [int(p_) for p_ in parts[1:] if p_.isdigit()]
        yr = next((n for n in nums if n > 31), None)
        day = next((n for n in nums if n <= 31), 1)
        if yr:
            try:
                return date(yr, mo, day)
            except ValueError:
                return None
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
    """rows: [{end, ocf, capex}] any order. Returns (ttm_ocf, ttm_capex, quarters newest-first, note)."""
    recs, bad = [], 0
    for r in rows or []:
        e, o = d(r.get("end")), f(r.get("ocf"))
        if e is None or o is None:
            WARN.append(f"cash-flow row unreadable: {r}")
            bad += 1
            continue
        recs.append({"end": e, "ocf": o, "capex": abs(f(r.get("capex")) or 0.0)})
    if bad:  # never build TTM around a hole: a dropped newest quarter would silently shift the window
        return None, None, [], f"{bad} unreadable cash-flow row(s): fix and rerun"
    recs.sort(key=lambda r: r["end"], reverse=True)
    if not recs:
        return None, None, [], "no cash-flow rows"
    if mode == "discrete":
        qs = recs[:4]
        if len(qs) < 4:
            return None, None, qs, "fewer than 4 readable discrete quarters"
        gaps = [abs(months(b["end"], a["end"]) - 3) > 1 for a, b in zip(qs, qs[1:])]
        if any(gaps):
            return None, None, qs, "the 4 newest readable quarters aren't consecutive (a row is missing or unreadable)"
        return sum(r["ocf"] for r in qs), sum(r["capex"] for r in qs), qs, "discrete quarters summed"
    if not fy_end:
        return None, None, [], "cf_mode ytd needs fy_end"
    for r in recs:
        r["fq"] = fiscal_q(r["end"], fy_end)
    # discrete quarters: Q1 = YTD; otherwise YTD minus the previous quarter's YTD (3 months earlier)
    qs = []
    for i, r in enumerate(recs):
        if r["ocf"] is None:
            continue
        if r["fq"] == 1:
            qs.append({"end": r["end"], "ocf": r["ocf"], "capex": r["capex"]})
        elif i + 1 < len(recs) and recs[i + 1]["ocf"] is not None and abs(months(recs[i + 1]["end"], r["end"]) - 3) <= 1:
            o = recs[i + 1]
            qs.append({"end": r["end"], "ocf": r["ocf"] - o["ocf"], "capex": r["capex"] - o["capex"]})
    L = recs[0]
    if L["ocf"] is None:
        return None, None, qs, "latest cash-flow row empty"
    if L["fq"] == 4:
        return L["ocf"], L["capex"], qs, f"latest row is fiscal year {L['end']}"
    fy = next((r for r in recs[1:] if r["fq"] == 4 and r["ocf"] is not None), None)
    prior = next((r for r in recs[1:] if abs(months(r["end"], L["end"]) - 12) <= 1 and r["ocf"] is not None), None)
    if fy and prior:
        return (L["ocf"] + fy["ocf"] - prior["ocf"], L["capex"] + fy["capex"] - prior["capex"], qs,
                f"TTM = YTD {L['end']} + FY {fy['end']} - prior YTD {prior['end']}")
    if len(qs) >= 4:
        q4 = qs[:4]
        return sum(r["ocf"] for r in q4), sum(r["capex"] for r in q4), qs, "TTM = last 4 de-cumulated quarters"
    return None, None, qs, "not enough YTD rows for TTM (pass 5 quarterly rows)"


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
def _to_millions(x):
    """statement_units 'thousands' (Yahoo financials) -> $ millions for every statement money field."""
    if str(x.get("statement_units", "millions")).lower() != "thousands":
        return x
    k = lambda v: None if f(v) is None else f(v) / 1000.0  # noqa: E731
    x = dict(x)
    for key in ("cash", "debt", "sbc_ttm"):
        if key in x:
            x[key] = k(x[key])
    for key, fields in (("cf_q", ("ocf", "capex")), ("annual", ("ocf", "capex", "ni")),
                        ("is_q", ("rev", "op_inc", "ni"))):
        x[key] = [{**r, **{fl: k(r[fl]) for fl in fields if fl in r}} for r in x.get(key) or []]
    return x


def valu(x):
    del WARN[:]
    x = _to_millions(x)
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
    sur = [s for s in (x.get("surprises") or []) if f(s.get("act")) is not None and f(s.get("est")) is not None][-4:]
    beats = sum(1 for s in sur if f(s["act"]) >= f(s["est"]))
    avg_sur = (sum((f(s["act"]) - f(s["est"])) / abs(f(s["est"])) for s in sur if f(s["est"])) / len(sur)) if sur else None
    sales_q = [f(v) for v in (x.get("sales_q") or [])]
    for r in x.get("is_q") or []:
        if d(r.get("end")) is None or f(r.get("rev")) is None:
            WARN.append(f"income-statement row unreadable, not used: {r}")
    revs = [f(r.get("rev")) for r in sorted((r for r in (x.get("is_q") or []) if d(r.get("end")) and f(r.get("rev")) is not None), key=lambda r: d(r["end"]))]
    if len(revs) > len(sales_q) and None not in revs:
        sales_q = revs  # discrete income-statement quarters win over a shorter sales_q list
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
    isq = sorted((r for r in (x.get("is_q") or []) if d(r.get("end"))), key=lambda r: d(r["end"]))[-4:]
    ni_ttm = sum(f(r.get("ni")) for r in isq) if len(isq) == 4 and all(f(r.get("ni")) is not None for r in isq) else None
    eps_gaap_ttm = sum(f(r.get("eps")) for r in isq) if len(isq) == 4 and all(f(r.get("eps")) is not None for r in isq) else None
    eps_adj_ttm = sum(eps_q[-4:]) if len(eps_q) >= 4 and None not in eps_q[-4:] else None
    margins = [f(r.get("op_inc")) / f(r.get("rev")) for r in isq if f(r.get("op_inc")) is not None and f(r.get("rev"))]
    print(f"Earnings (last {len(sur)}): beats {beats}/{len(sur)} | avg EPS surprise {p(avg_sur)} | "
          f"sales YoY {' / '.join(p(v, 0) for v in s_yoy)} -> {trend} | adj EPS YoY {' / '.join(p(v, 0) for v in e_yoy)} | "
          f"op margin {' / '.join(pa(v, 0) for v in margins) or 'n/a'}"
          f"{'' if f(x.get('est_rev_4wk')) is None else ' | FY EPS est 4wk ' + p(f(x.get('est_rev_4wk')) / 100)}")

    # ---- 2. owner cash flow ----
    ocf, capex, qs, cf_note = cf_series(x.get("cf_q"), fy_end, x.get("cf_mode", "ytd"))
    fcf = (ocf - capex) if (ocf is not None and capex is not None) else None
    owner = (fcf - sbc) if (fcf is not None and sbc is not None) else None
    if owner is None and not fin:
        unver.append("owner FCF (OCF/CapEx/SBC)")
    conv = owner / ni_ttm if (owner is not None and ni_ttm and ni_ttm > 0) else None
    gap = (eps_adj_ttm / eps_gaap_ttm - 1) if (eps_adj_ttm and eps_gaap_ttm and eps_gaap_ttm > 0) else None
    print(f"Owner cash: OCF {bigm(ocf)} - CapEx {bigm(capex)} - SBC {bigm(sbc)} = owner FCF {bigm(owner)} "
          f"({cf_note}) | SBC/OCF {pa(sbc / ocf if (sbc is not None and ocf) else None)} | owner FCF / GAAP NI "
          f"{m(conv)}x | adj EPS vs GAAP {p(gap, 0)}")
    if qs:
        print("  quarters (de-cumulated, newest first): " +
              " | ".join(f"{r['end']} OCF {bigm(r['ocf'])} capex {bigm(r['capex'])}" for r in qs[:4]))
    quality = "n/a"
    if conv is not None or gap is not None:
        bad = (conv is not None and conv < 0.7) or (gap is not None and gap > 0.40) or \
              (sbc is not None and ocf and sbc / ocf > 0.25)
        quality = "LOW (cash or GAAP gap)" if bad else "OK"

    # ---- 3. market: stock vs S&P (s_chg*) and peers; residual after beta x S&P ----
    pc = lambda k: (f(x.get(k)) / 100) if f(x.get(k)) is not None else None
    t4, t12, rel4, rel12 = pc("t_chg4w"), pc("t_chg12w"), pc("t_rel4w"), pc("t_rel12w")
    # S&P move: given directly (SPY's own % change), else backed out of an S&P-relative change
    s4, s12 = pc("s_chg4w"), pc("s_chg12w")
    if s4 is None and t4 is not None and rel4 is not None:
        s4 = (1 + t4) / (1 + rel4) - 1
    if s12 is None and t12 is not None and rel12 is not None:
        s12 = (1 + t12) / (1 + rel12) - 1
    # % changes measured to an older close: re-mark the stock's leg to the live spot (ref_px = that close)
    zpx = f(x.get("ref_px", x.get("zacks_px")))
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
          + (f" | stock leg re-marked to spot ({p(remark - 1)} vs ref close {m(zpx)})" if remark else ""))

    # ---- 4. valuation ----
    rf = rate(x.get("rf")) or 0.045
    erp = rate(x.get("erp")) or 0.05
    r = min(0.14, max(0.07, rf + (beta if beta is not None else 1.0) * erp))
    ev = (mcap + (debt or 0) - (cash or 0)) if mcap else None
    if debt is None or cash is None:
        unver.append("cash/debt")
    eq = (lambda e: (e - (debt or 0) + (cash or 0)) / shares if (e is not None and shares) else None)
    eps_f1, eps_f2 = f(x.get("eps_f1")), f(x.get("eps_f2"))
    cands = [v for v in ((eps_f2 / eps_f1 - 1) if (eps_f1 and eps_f2 and eps_f1 > 0) else None, ttm_sales_g) if v is not None]
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
    v_bear = eq(dcf_ev(owner, g_bear, r + 0.01)) if dcf_ok else None
    v_base = eq(dcf_ev(owner, g_base, r)) if dcf_ok else None
    v_bull = eq(dcf_ev(owner, g_bull, r - 0.005)) if dcf_ok else None
    v_base_up = eq(dcf_ev(owner, g_base, r + 0.01)) if dcf_ok else None
    ig = implied_g(owner, ev, r) if dcf_ok else None
    ig_up = implied_g(owner, ev, r + 0.01) if dcf_ok else None
    if not dcf_ok and not fin:
        print("DCF: n/m - owner FCF <= 0 or missing (no owner cash to discount)")
    print(f"Rates: r = rf {pa(rf)}{'' if x.get('rf') is not None else ' (ASSUMED)'} + beta x ERP {pa(erp)} = {pa(r)} | "
          f"+100bp -> base value {p((v_base_up / v_base - 1) if (v_base and v_base_up) else None)}")
    print(f"Reverse DCF: price implies {p(ig)} owner-FCF growth/yr for 5y (fading to {pa(GT)}) at r {pa(r)}; "
          f"{p(ig_up)} at r +1% | inputs: EPS F1->F2 {p((eps_f2 / eps_f1 - 1) if (eps_f1 and eps_f2 and eps_f1 > 0) else None)}, "
          f"TTM sales {p(ttm_sales_g)}")
    print(f"DCF/sh: bear {m(v_bear)} (g {p(g_bear)}, r {pa(r + 0.01)}) | base {m(v_base)} (g {p(g_base)}) | "
          f"bull {m(v_bull)} (g {p(g_bull)}, r {pa(r - 0.005)})")

    # own history: P/FCF at each fiscal year's low (current share count: buybacks make past multiples look lower -> conservative)
    pm = x.get("px_m") or {}
    bars = []
    for t, lo in zip(pm.get("t") or [], pm.get("l") or []):
        dt, lv = d(t), f(lo)
        if dt is None or lv is None:
            WARN.append(f"monthly bar unreadable, not used: {t} {lo}")
            continue
        bars.append((dt.replace(day=1), lv))
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
    pfcf = mcap / fcf if (mcap and fcf and fcf > 0) else None
    powner = mcap / owner if (mcap and owner and owner > 0) else None
    v_trough = trough * owner / shares if (trough and owner and owner > 0 and shares) else None
    v_hmed = hmed * fcf / shares if (hmed and fcf and fcf > 0 and shares) else None
    print(f"Own history ({len(hist)} FY): P/FCF at yearly lows {' / '.join(f'{e.year} {v:.1f}x' for e, v in hist) or 'n/a'} | "
          f"trough {m(trough, 1)}x median {m(hmed, 1)}x | now P/FCF {m(pfcf, 1)}x P/owner-FCF {m(powner, 1)}x | "
          f"trough x owner FCF = {m(v_trough)}/sh | median x FCF = {m(v_hmed)}/sh")

    # peers
    # Finviz Forward P/E is on NEXT fiscal year EPS -> pe_f2, matched with eps_f2; Zacks-style pe_f1 -> eps_f1
    pe_key = "pe_f2" if any(f(q.get("pe_f2")) for q in peers) else "pe_f1"
    eps_pe = eps_f2 if pe_key == "pe_f2" else eps_f1
    pe_med = median([f(q.get(pe_key)) for q in peers if (f(q.get(pe_key)) or 0) > 0])
    ps_med = median([f(q.get("ps")) for q in peers if (f(q.get("ps")) or 0) > 0])
    peg_med = median([f(q.get("peg")) for q in peers if (f(q.get("peg")) or 0) > 0])
    v_pe = pe_med * eps_pe if (pe_med and eps_pe and eps_pe > 0) else None
    v_ps = ps_med * sales_ttm / shares if (ps_med and sales_ttm and shares) else None
    t_pe = S / eps_pe if (S and eps_pe and eps_pe > 0) else None
    t_ps = mcap / sales_ttm if (mcap and sales_ttm) else None
    print(f"Peers ({', '.join(str(q.get('t')) for q in peers) or 'none'}): fwd P/E ({'next FY' if pe_key == 'pe_f2' else 'current FY'}) med {m(pe_med, 1)}x vs {m(t_pe, 1)}x "
          f"({p((t_pe / pe_med - 1) if (t_pe and pe_med) else None, 0)}) | P/S med {m(ps_med, 1)}x vs {m(t_ps, 1)}x | "
          f"PEG med {m(peg_med)} vs {m(f(x.get('peg')))} | implied/sh: fwd P/E {m(v_pe)} | P/S {m(v_ps)}")
    if not peers:
        unver.append("peers")

    # ---- verdict ----
    floor = min([v for v in (v_bear, v_trough) if v is not None], default=None)
    if fin:
        floor = None
    fair = median([v_base, v_hmed, v_pe])
    if fin and fair is None:
        fair = v_pe
    if not dcf_ok and not fin and fair is not None:
        fair = median([v_pe, v_ps])  # no owner cash: only market comparables left
    mos = (fair / S - 1) if (fair and S) else None
    if fair is None or S is None:
        v = "INCOMPLETE: fair value needs owner FCF, peers or estimates"
    elif owner is None and not fin:
        v = "INCOMPLETE: owner FCF inputs missing or unreadable - fix them; this is not a SPECULATIVE call"
    elif not dcf_ok and not fin:
        v = "SPECULATIVE: no owner cash flow - value rests on peer multiples only"
    elif floor is not None and abs(S / floor - 1) <= 0.02:
        v = f"AT FLOOR: spot within 2% of the floor ({p(S / floor - 1)}) - no cushion"
    elif floor is not None and S < floor:
        v = f"DEEP VALUE: spot {p(S / floor - 1)} below the floor"
    elif S < fair * 0.85:
        v = "UNDERVALUED"
    elif S <= fair * 1.15:
        v = "FAIRLY VALUED"
    else:
        v = "RICH"
    print(f"Range/sh: floor {m(floor)} | fair {m(fair)} | bull {m(v_bull)} | spot {m(S)} -> margin of safety {p(mos)} | "
          f"earnings {trend}, quality {quality}, move {cls}")
    if unver:
        print("UNVERIFIED: " + ", ".join(unver))
    if WARN:
        print("INPUT WARNINGS: " + " | ".join(WARN))
    print("VERDICT: " + v)
    hand = {"ticker": T_, "asof": str(asof), "val_floor": None if floor is None else round(floor, 2),
            "val_fair": None if fair is None else round(fair, 2), "val_implied_g": None if ig is None else round(ig, 4),
            "val_r": round(r, 4), "val_trough_pfcf": None if trough is None else round(trough, 1),
            "val_move": cls, "val_trend": trend, "val_verdict": v.split(":")[0],
            "input_warnings": len(WARN)}
    print("VALU_HANDOFF " + json.dumps(hand))


if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] != "valu":
        print(__doc__)
        sys.exit(1)
    valu(load(sys.argv[2]))
