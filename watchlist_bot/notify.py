"""Deliver the daily digest via Telegram and/or email; always echo to stdout."""
from __future__ import annotations

import datetime as dt
import html
import logging
import smtplib
from email.message import EmailMessage

import requests

from .config import Config
from .news import NewsItem
from .state import PositionDiff

log = logging.getLogger(__name__)
TELEGRAM_LIMIT = 4000


def build_digest(diff: PositionDiff, alerts: list[tuple[NewsItem, int, list[str]]]) -> str:
    today = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    lines = [f"<b>Portfolio watchlist — {today}</b>", f"Tracking {len(diff.held)}: {', '.join(sorted(diff.held)) or '—'}"]
    if diff.opened:
        lines.append(f"➕ Added (new positions): {', '.join(sorted(diff.opened))}")
    if diff.closed:
        lines.append(f"➖ Removed (closed): {', '.join(sorted(diff.closed))}")

    if not alerts:
        lines.append("\nNo material news.")
        return "\n".join(lines)

    lines.append(f"\n<b>Material news ({len(alerts)})</b>")
    by_ticker: dict[str, list[tuple[NewsItem, int, list[str]]]] = {}
    for a in alerts:
        by_ticker.setdefault(a[0].ticker, []).append(a)
    for ticker in sorted(by_ticker, key=lambda t: -max(s for _, s, _ in by_ticker[t])):
        lines.append(f"\n<b>{ticker}</b>")
        for item, s, tags in sorted(by_ticker[ticker], key=lambda a: -a[1]):
            when = dt.datetime.fromtimestamp(item.published, dt.timezone.utc).strftime("%m-%d")
            lines.append(
                f"• [{s}|{'/'.join(tags[:2])}] {html.escape(item.headline)} "
                f"<i>({html.escape(item.source)}, {when})</i> <a href=\"{html.escape(item.url)}\">link</a>"
            )
    return "\n".join(lines)


def _chunks(text: str, limit: int) -> list[str]:
    out, cur = [], ""
    for line in text.split("\n"):
        if len(cur) + len(line) + 1 > limit and cur:
            out.append(cur)
            cur = ""
        cur += line + "\n"
    if cur:
        out.append(cur)
    return out


def send(cfg: Config, digest: str) -> None:
    print(digest)

    if cfg.telegram_bot_token and cfg.telegram_chat_id:
        for chunk in _chunks(digest, TELEGRAM_LIMIT):
            r = requests.post(
                f"https://api.telegram.org/bot{cfg.telegram_bot_token}/sendMessage",
                json={"chat_id": cfg.telegram_chat_id, "text": chunk, "parse_mode": "HTML", "disable_web_page_preview": True},
                timeout=20,
            )
            if not r.ok:
                log.error("Telegram send failed: %s %s", r.status_code, r.text[:200])

    if cfg.smtp_host and cfg.email_to:
        msg = EmailMessage()
        msg["Subject"] = "Portfolio watchlist digest"
        msg["From"] = cfg.smtp_user or cfg.email_to
        msg["To"] = cfg.email_to
        msg.set_content("HTML digest attached.")
        msg.add_alternative(digest.replace("\n", "<br>\n"), subtype="html")
        with smtplib.SMTP(cfg.smtp_host, cfg.smtp_port, timeout=30) as s:
            s.starttls()
            if cfg.smtp_user:
                s.login(cfg.smtp_user, cfg.smtp_password)
            s.send_message(msg)
