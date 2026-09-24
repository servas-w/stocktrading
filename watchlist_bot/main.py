"""Daily run: sync Robinhood watchlist with open positions, then alert on material news.

    python -m watchlist_bot                 # full run
    python -m watchlist_bot --dry-run       # no watchlist writes, no notifications, no state save
    python -m watchlist_bot --tickers MRNA,PFE --dry-run   # skip Robinhood, test news only
"""
from __future__ import annotations

import argparse
import logging
import time

from . import materiality, notify
from .config import Config
from .news import FinnhubNews, NewsItem, SecFilings
from .state import State, diff_positions

log = logging.getLogger("watchlist_bot")


def collect_alerts(
    tickers: set[str], since: float, state: State, cfg: Config
) -> list[tuple[NewsItem, int, list[str]]]:
    sources = [FinnhubNews(cfg.finnhub_api_key), SecFilings(cfg.sec_user_agent)]
    alerts = []
    for ticker in sorted(tickers):
        for src in sources:
            try:
                items = src.fetch(ticker, since)
            except Exception as e:  # one bad source/ticker shouldn't kill the run
                log.warning("%s failed for %s: %s", type(src).__name__, ticker, e)
                continue
            for item in items:
                if item.id in state.seen:
                    continue
                s, tags = materiality.score(item)
                if s >= cfg.min_materiality:
                    alerts.append((item, s, tags))
        time.sleep(0.2)  # stay well under Finnhub (60/min) and SEC (10/s) limits
    return alerts


def run(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="watchlist_bot")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--tickers", help="comma-separated override; skips Robinhood entirely")
    args = ap.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    cfg = Config.from_env()
    state = State.load(cfg.state_path)
    now = time.time()

    if args.tickers:
        current = {t.strip().upper() for t in args.tickers.split(",") if t.strip()}
        diff = diff_positions(state.tracked, current)
    else:
        from .broker import Robinhood  # imported lazily so --tickers works without credentials

        rh = Robinhood(cfg)
        rh.login()
        try:
            current = rh.open_tickers()
            diff = diff_positions(state.tracked, current)
            log.info("Held: %s | opened: %s | closed: %s", sorted(current), sorted(diff.opened), sorted(diff.closed))
            if not args.dry_run:
                on_list = rh.watchlist_symbols()
                rh.add_to_watchlist(current - on_list)
                rh.remove_from_watchlist(diff.closed & on_list)
        finally:
            rh.logout()

    since = now - cfg.lookback_hours * 3600
    alerts = collect_alerts(diff.held, since, state, cfg)
    digest = notify.build_digest(diff, alerts)

    if args.dry_run:
        print(digest)
        return 0

    notify.send(cfg, digest)
    for item, _, _ in alerts:
        state.seen[item.id] = now
    state.tracked = set(diff.held)
    state.last_run = now
    state.prune_seen(now)
    state.save(cfg.state_path)
    return 0
