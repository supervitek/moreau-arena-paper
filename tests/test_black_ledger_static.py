from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "web" / "static" / "black-ledger"


def test_black_ledger_public_door_is_complete_and_unlisted() -> None:
    html = (STATIC / "index.html").read_text(encoding="utf-8")
    app_source = (ROOT / "web" / "app.py").read_text(encoding="utf-8")

    assert 'data-i18n="heroA">WE SET OUT TO FIND<' in html
    assert 'data-i18n="heroB">THE MOST DEVIOUS AI.<' in html
    assert "We think we found it." in html
    assert "THE MOST DEVIOUS" in html
    assert "How we turned numbers into accusations." in html
    assert "https://moreauarena.com/static/black-ledger/og-season-01.png" in html
    assert (STATIC / "og-season-01.png").stat().st_size > 100_000
    assert '@app.get("/black-ledger")' in app_source
    assert '@app.get("/black-ledger/")' in app_source
    assert "/black-ledger" not in (ROOT / "web" / "static" / "index.html").read_text(encoding="utf-8")
