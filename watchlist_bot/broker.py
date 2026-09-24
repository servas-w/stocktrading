"""Robinhood access: read open positions and maintain a watchlist.

Uses the unofficial `robin_stocks` client. Tickers are collected from both
open stock positions and the underlyings of open option positions (short puts,
spreads, etc.), since an options position carries the same news risk.
"""
from __future__ import annotations

import logging
from typing import Iterable

import pyotp
import robin_stocks.robinhood as rh

from .config import Config

log = logging.getLogger(__name__)


class Robinhood:
    def __init__(self, cfg: Config):
        self.cfg = cfg

    def login(self) -> None:
        if not (self.cfg.rh_username and self.cfg.rh_password):
            raise RuntimeError("RH_USERNAME / RH_PASSWORD are not set")
        mfa = pyotp.TOTP(self.cfg.rh_totp_secret).now() if self.cfg.rh_totp_secret else None
        rh.login(
            username=self.cfg.rh_username,
            password=self.cfg.rh_password,
            mfa_code=mfa,
            store_session=True,
        )

    def logout(self) -> None:
        try:
            rh.logout()
        except Exception:  # logout failure is harmless
            pass

    def open_tickers(self) -> set[str]:
        """Every ticker with a non-zero stock or option position."""
        tickers: set[str] = set()

        for pos in rh.account.get_open_stock_positions() or []:
            if float(pos.get("quantity") or 0) == 0:
                continue
            symbol = pos.get("symbol") or rh.stocks.get_symbol_by_url(pos["instrument"])
            if symbol:
                tickers.add(symbol.upper())

        for pos in rh.options.get_open_option_positions() or []:
            if float(pos.get("quantity") or 0) == 0:
                continue
            symbol = pos.get("chain_symbol")
            if symbol:
                tickers.add(symbol.upper())

        return tickers

    def watchlist_symbols(self) -> set[str]:
        items = rh.account.get_watchlist_by_name(self.cfg.rh_watchlist_name) or {}
        results = items.get("results", []) if isinstance(items, dict) else items
        return {i["symbol"].upper() for i in results if i.get("symbol")}

    def add_to_watchlist(self, symbols: Iterable[str]) -> None:
        symbols = sorted(symbols)
        if symbols:
            log.info("Adding to watchlist %r: %s", self.cfg.rh_watchlist_name, symbols)
            rh.account.post_symbols_to_watchlist(symbols, name=self.cfg.rh_watchlist_name)

    def remove_from_watchlist(self, symbols: Iterable[str]) -> None:
        symbols = sorted(symbols)
        if symbols:
            log.info("Removing from watchlist %r: %s", self.cfg.rh_watchlist_name, symbols)
            rh.account.delete_symbols_from_watchlist(symbols, name=self.cfg.rh_watchlist_name)
