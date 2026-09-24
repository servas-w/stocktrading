from watchlist_bot.state import SEEN_TTL_SECONDS, State, diff_positions


def test_diff_positions():
    d = diff_positions({"AAPL", "MRNA"}, {"MRNA", "NVDA"})
    assert d.opened == {"NVDA"}
    assert d.closed == {"AAPL"}
    assert d.held == {"MRNA", "NVDA"}


def test_state_roundtrip(tmp_path):
    p = tmp_path / "s" / "state.json"
    s = State(tracked={"PFE"}, seen={"sec:1": 100.0}, last_run=123.0)
    s.save(str(p))
    loaded = State.load(str(p))
    assert loaded.tracked == {"PFE"}
    assert loaded.seen == {"sec:1": 100.0}
    assert loaded.last_run == 123.0


def test_load_missing_returns_empty(tmp_path):
    assert State.load(str(tmp_path / "nope.json")).tracked == set()


def test_prune_seen():
    now = 10 * SEEN_TTL_SECONDS
    s = State(seen={"old": now - SEEN_TTL_SECONDS - 1, "new": now - 10})
    s.prune_seen(now)
    assert set(s.seen) == {"new"}
