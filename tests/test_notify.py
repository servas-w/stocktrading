from watchlist_bot.news import NewsItem
from watchlist_bot.notify import _chunks, build_digest
from watchlist_bot.state import diff_positions


def test_digest_lists_changes_and_escapes():
    d = diff_positions({"AAPL"}, {"MRNA"})
    n = NewsItem(id="1", ticker="MRNA", source="Reuters", headline="FDA <approves> drug",
                 summary="", url="https://x", published=0)
    out = build_digest(d, [(n, 5, ["FDA"])])
    assert "Added (new positions): MRNA" in out
    assert "Removed (closed): AAPL" in out
    assert "&lt;approves&gt;" in out


def test_digest_no_news():
    assert "No material news" in build_digest(diff_positions(set(), {"X"}), [])


def test_chunks_respect_limit():
    text = "\n".join("x" * 50 for _ in range(100))
    assert all(len(c) <= 200 for c in _chunks(text, 200))
