"""Rule-based materiality scoring. Score >= MIN_MATERIALITY gets an alert.

Weights are tuned toward what moves a short-premium book: binary biotech
catalysts, dilution, M&A, guidance, and solvency/listing risk.
"""
from __future__ import annotations

import re

from .news import NewsItem

# (pattern, score, tag)
KEYWORDS: list[tuple[str, int, str]] = [
    # Biotech / regulatory binaries
    (r"\bfda (approv|accept|clear)", 5, "FDA"),
    (r"complete response letter|\bCRL\b", 5, "FDA"),
    (r"\bpdufa\b", 4, "FDA"),
    (r"advisory committee|\badcomm\b", 4, "FDA"),
    (r"clinical hold", 5, "FDA"),
    (r"refuse to file|\bRTF\b", 5, "FDA"),
    (r"breakthrough therapy|fast track|priority review|accelerated approval", 3, "FDA"),
    (r"top-?line|primary endpoint|phase (3|iii|2b|2|ii)\b.*(result|data|readout)", 4, "Trial"),
    (r"(fail|miss)(ed|s)? .*endpoint|did not meet", 5, "Trial"),
    # Capital structure
    (r"public offering|registered direct|at-the-market|\bATM\b|private placement", 4, "Dilution"),
    (r"pre-funded warrant|convertible (note|senior)", 4, "Dilution"),
    (r"reverse (stock )?split", 4, "Dilution"),
    (r"share (buyback|repurchase)", 2, "Capital"),
    (r"dividend (cut|suspend|eliminat)", 4, "Capital"),
    # Corporate events
    (r"\b(to acquire|acquisition of|to be acquired|merger|takeover|tender offer|buyout)\b", 5, "M&A"),
    (r"strategic alternatives", 4, "M&A"),
    (r"\b(raises|lowers|cuts|withdraws|reaffirms) (its )?(full-year |fy\d* )?guidance", 4, "Guidance"),
    (r"(earnings|quarterly results|q[1-4] results)", 2, "Earnings"),
    (r"(beats|misses) (estimates|expectations)", 3, "Earnings"),
    (r"\b(ceo|cfo|chief executive|chief financial)\b.*(resign|step down|depart|terminat|appoint)", 4, "Mgmt"),
    # Distress / legal
    (r"bankruptcy|chapter 11|going concern", 5, "Distress"),
    (r"delist|nasdaq (notice|deficiency)|minimum bid", 4, "Listing"),
    (r"restate|accounting irregular|material weakness", 5, "Accounting"),
    (r"\bsec (investigation|probe|charges)|subpoena|doj\b|class action", 3, "Legal"),
    (r"trading halt|halted", 4, "Halt"),
    (r"recall", 3, "Product"),
    # Street
    (r"\b(downgrade|upgrade)[sd]?\b", 2, "Analyst"),
    (r"short (seller|report)", 4, "Short report"),
]
_COMPILED = [(re.compile(p, re.I), s, t) for p, s, t in KEYWORDS]

# SEC form -> (score, tag)
FORMS: dict[str, tuple[int, str]] = {
    "S-1": (4, "Dilution"),
    "S-3": (4, "Dilution"),
    "S-3ASR": (4, "Dilution"),
    "424B5": (4, "Dilution"),
    "424B4": (4, "Dilution"),
    "424B3": (3, "Dilution"),
    "SC 13D": (4, "Activist"),
    "SC 13D/A": (3, "Activist"),
    "SCHEDULE 13D": (4, "Activist"),
    "SC TO-T": (5, "M&A"),
    "DEFM14A": (5, "M&A"),
    "10-K": (3, "Annual report"),
    "10-Q": (2, "Quarterly report"),
    "NT 10-K": (5, "Late filing"),
    "NT 10-Q": (5, "Late filing"),
    "25-NSE": (5, "Delisting"),
}

# 8-K item -> (score, tag)
EIGHT_K_ITEMS: dict[str, tuple[int, str]] = {
    "1.01": (4, "Material agreement"),
    "1.03": (5, "Bankruptcy"),
    "2.01": (5, "M&A closed"),
    "2.02": (3, "Earnings"),
    "2.05": (4, "Restructuring"),
    "2.06": (4, "Impairment"),
    "3.01": (5, "Listing"),
    "3.02": (4, "Dilution"),
    "4.01": (4, "Auditor change"),
    "4.02": (5, "Restatement"),
    "5.02": (3, "Mgmt"),
    "8.01": (3, "Other event"),
}


def score(item: NewsItem) -> tuple[int, list[str]]:
    """Return (score, tags). Score is the max single signal, +1 per extra distinct tag."""
    hits: dict[str, int] = {}

    def hit(s: int, tag: str) -> None:
        hits[tag] = max(hits.get(tag, 0), s)

    if item.form:
        form = item.form.upper()
        if form in FORMS:
            hit(*FORMS[form])
        if form.startswith("8-K") or form.startswith("6-K"):
            for code in (c.strip() for c in item.items.split(",") if c.strip()):
                if code in EIGHT_K_ITEMS:
                    hit(*EIGHT_K_ITEMS[code])
            if form.startswith("6-K"):
                hit(2, "Foreign filer report")

    text = f"{item.headline} {item.summary}"
    for rx, s, tag in _COMPILED:
        if rx.search(text):
            hit(s, tag)

    if not hits:
        return 0, []
    tags = sorted(hits, key=lambda t: -hits[t])
    return max(hits.values()) + (len(hits) - 1), tags
