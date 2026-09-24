"""News sources: Finnhub company news and SEC EDGAR filings."""
from __future__ import annotations

import datetime as dt
import logging
from dataclasses import dataclass

import requests

log = logging.getLogger(__name__)
TIMEOUT = 20


@dataclass(frozen=True)
class NewsItem:
    id: str
    ticker: str
    source: str
    headline: str
    summary: str
    url: str
    published: float  # unix seconds
    form: str = ""  # SEC form type, empty for articles
    items: str = ""  # 8-K item numbers, e.g. "2.02,9.01"


class FinnhubNews:
    URL = "https://finnhub.io/api/v1/company-news"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def fetch(self, ticker: str, since: float) -> list[NewsItem]:
        if not self.api_key:
            return []
        start = dt.datetime.fromtimestamp(since, dt.timezone.utc).date()
        end = dt.datetime.now(dt.timezone.utc).date()
        resp = requests.get(
            self.URL,
            params={"symbol": ticker, "from": start.isoformat(), "to": end.isoformat(), "token": self.api_key},
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        out = []
        for a in resp.json() or []:
            ts = float(a.get("datetime") or 0)
            if ts < since:
                continue
            out.append(
                NewsItem(
                    id=f"finnhub:{a.get('id') or a.get('url')}",
                    ticker=ticker,
                    source=a.get("source") or "Finnhub",
                    headline=a.get("headline") or "",
                    summary=a.get("summary") or "",
                    url=a.get("url") or "",
                    published=ts,
                )
            )
        return out


class SecFilings:
    """Recent EDGAR filings for a ticker. Free; SEC asks for a contact User-Agent."""

    TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
    SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik:010d}.json"
    ARCHIVE_URL = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/{doc}"

    def __init__(self, user_agent: str):
        self.headers = {"User-Agent": user_agent or "portfolio-watchlist-bot admin@example.com"}
        self._cik_map: dict[str, int] | None = None

    def _cik(self, ticker: str) -> int | None:
        if self._cik_map is None:
            resp = requests.get(self.TICKERS_URL, headers=self.headers, timeout=TIMEOUT)
            resp.raise_for_status()
            self._cik_map = {v["ticker"].upper(): int(v["cik_str"]) for v in resp.json().values()}
        return self._cik_map.get(ticker.upper())

    def fetch(self, ticker: str, since: float) -> list[NewsItem]:
        cik = self._cik(ticker)
        if cik is None:  # ETFs, ADRs without EDGAR filings, etc.
            return []
        resp = requests.get(self.SUBMISSIONS_URL.format(cik=cik), headers=self.headers, timeout=TIMEOUT)
        resp.raise_for_status()
        recent = resp.json().get("filings", {}).get("recent", {})
        since_date = dt.datetime.fromtimestamp(since, dt.timezone.utc).date().isoformat()

        out = []
        for i, form in enumerate(recent.get("form", [])):
            filed = recent["filingDate"][i]
            if filed < since_date:
                break  # newest first
            acc = recent["accessionNumber"][i]
            doc = recent["primaryDocument"][i]
            desc = recent.get("primaryDocDescription", [""] * (i + 1))[i] or ""
            items = recent.get("items", [""] * (i + 1))[i] or ""
            out.append(
                NewsItem(
                    id=f"sec:{acc}",
                    ticker=ticker,
                    source="SEC EDGAR",
                    headline=f"{form} filed" + (f" (items {items})" if items else "") + (f": {desc}" if desc else ""),
                    summary="",
                    url=self.ARCHIVE_URL.format(cik=cik, acc=acc.replace("-", ""), doc=doc),
                    published=dt.datetime.fromisoformat(filed).replace(tzinfo=dt.timezone.utc).timestamp(),
                    form=form,
                    items=items,
                )
            )
        return out
