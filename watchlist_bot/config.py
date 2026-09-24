"""Runtime configuration, read from environment variables (see .env.example)."""
from __future__ import annotations

import os
from dataclasses import dataclass


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


@dataclass(frozen=True)
class Config:
    rh_username: str
    rh_password: str
    rh_totp_secret: str
    rh_watchlist_name: str
    finnhub_api_key: str
    sec_user_agent: str
    telegram_bot_token: str
    telegram_chat_id: str
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    email_to: str
    state_path: str
    min_materiality: int
    lookback_hours: int

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            rh_username=_env("RH_USERNAME"),
            rh_password=_env("RH_PASSWORD"),
            rh_totp_secret=_env("RH_TOTP_SECRET"),
            rh_watchlist_name=_env("RH_WATCHLIST_NAME", "Portfolio"),
            finnhub_api_key=_env("FINNHUB_API_KEY"),
            sec_user_agent=_env("SEC_USER_AGENT"),
            telegram_bot_token=_env("TELEGRAM_BOT_TOKEN"),
            telegram_chat_id=_env("TELEGRAM_CHAT_ID"),
            smtp_host=_env("SMTP_HOST"),
            smtp_port=int(_env("SMTP_PORT", "587")),
            smtp_user=_env("SMTP_USER"),
            smtp_password=_env("SMTP_PASSWORD"),
            email_to=_env("EMAIL_TO"),
            state_path=_env("STATE_PATH", "state/state.json"),
            min_materiality=int(_env("MIN_MATERIALITY", "3")),
            lookback_hours=int(_env("LOOKBACK_HOURS", "36")),
        )
