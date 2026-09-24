# Robinhood Portfolio Watchlist Bot

> **Current setup:** the daily job runs as a **Claude routine** that uses the Robinhood and Gmail connectors, on weekdays at 12:00 UTC (19:00 Da Nang). The prompt it runs is in [`ROUTINE.md`](ROUTINE.md). Robinhood dropped authenticator-app 2FA, so the self-hosted Python version below can no longer log in unattended. It stays here as a manual/local fallback, and its GitHub schedule is turned off.

Runs once a day and:

1. **Reads your open Robinhood positions**: stocks, plus the underlying of every open option position (short puts, credit spreads, etc.).
2. **Syncs a Robinhood watchlist.** New positions get added. When a position closes, the ticker is removed. It only removes tickers the bot added itself, so any symbols you add to the list by hand stay put.
3. **Scans for material news** on every held ticker from:
   - **Finnhub** company news (free API key)
   - **SEC EDGAR** filings (8-K items, S-1/S-3/424B dilution, 13D, NT 10-K/Q, delisting notices…)
4. **Scores the news** with rules tuned for a short-premium book: FDA/PDUFA/CRL, trial readouts, offerings/ATMs/reverse splits, M&A, guidance, going-concern and delisting risk, restatements, halts and short reports. Anything scoring ≥ `MIN_MATERIALITY` goes out in one digest by **Telegram** and/or **email**. Each item is sent only once.

## Setup

### 1. Robinhood
- Create a custom watchlist in the app named **`Portfolio`**, or set `RH_WATCHLIST_NAME`.
- Turn on 2FA with an **authenticator app** and save the base32 setup key. That key is `RH_TOTP_SECRET`, and it lets the bot log in without you.

> ⚠️ This uses the unofficial `robin_stocks` API. Robinhood can change it or ask for device verification at any time. Give the bot a strong, unique password.

### 2. News and notifications
- Finnhub key: https://finnhub.io (the free tier is enough).
- `SEC_USER_AGENT`: `"Your Name you@email.com"` (SEC policy).
- Telegram: message `@BotFather` to create a bot, which gives you the token. Send the bot one message, then open `https://api.telegram.org/bot<TOKEN>/getUpdates` to find your chat id.

### 3. Run it daily (GitHub Actions)
Add these under **Settings → Secrets and variables → Actions**:

| Secrets | Variables (optional) |
|---|---|
| `RH_USERNAME`, `RH_PASSWORD`, `RH_TOTP_SECRET` | `RH_WATCHLIST_NAME` (default `Portfolio`) |
| `FINNHUB_API_KEY` | `SEC_USER_AGENT` |
| `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | `MIN_MATERIALITY` (default `3`) |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `EMAIL_TO` (optional) | |

The workflow runs on weekdays at **12:00 UTC**. That is 19:00 in Da Nang and 08:00 in New York, before the US open. To run it by hand, go to **Actions → Daily portfolio watchlist → Run workflow** and tick *dry run* for the first try.

State is kept in the Actions cache, not in git, so your holdings never end up in the repo's history.

## Local use

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env   # fill in, then: set -a; . ./.env; set +a

python -m watchlist_bot --dry-run                   # read positions, print digest, change nothing
python -m watchlist_bot --tickers MRNA,NVDA --dry-run   # skip Robinhood, test news only
python -m watchlist_bot                             # full run
pytest -q
```

## Layout

```
watchlist_bot/
  broker.py       Robinhood login, positions (stock + option underlyings), watchlist add/remove
  news.py         Finnhub + SEC EDGAR fetchers
  materiality.py  keyword / SEC form / 8-K item scoring
  notify.py       digest builder, Telegram + SMTP
  state.py        tracked tickers, seen-news dedupe, position diff
  main.py         orchestration / CLI
```

## Tuning
- Edit the weights in `watchlist_bot/materiality.py`. Scoring takes the strongest signal and adds +1 for each extra distinct category.
- `LOOKBACK_HOURS` (default 36) sets how far back each run looks. Items already sent are skipped.
