from watchlist_bot.materiality import score
from watchlist_bot.news import NewsItem


def item(headline="", form="", items="", summary=""):
    return NewsItem(id="x", ticker="T", source="s", headline=headline, summary=summary,
                    url="u", published=0, form=form, items=items)


def test_crl_is_high():
    s, tags = score(item("Company receives Complete Response Letter from FDA"))
    assert s >= 5 and "FDA" in tags


def test_offering_is_dilution():
    s, tags = score(item("XYZ announces pricing of $150M public offering"))
    assert s >= 4 and tags[0] == "Dilution"


def test_noise_scores_zero():
    assert score(item("5 stocks to watch this week"))[0] == 0


def test_8k_items():
    s, tags = score(item("8-K filed", form="8-K", items="2.02,9.01"))
    assert s == 3 and tags == ["Earnings"]


def test_s3_form():
    s, tags = score(item("S-3 filed", form="S-3"))
    assert s == 4 and "Dilution" in tags


def test_multiple_tags_bonus():
    s, _ = score(item("Biotech announces topline Phase 3 results and public offering"))
    assert s == 5  # max 4 + 1 extra tag
