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


def test_black_ledger_seasons_03_through_05_are_show_first_and_routed() -> None:
    season_03 = (STATIC / "season-03.html").read_text(encoding="utf-8")
    season_04 = (STATIC / "season-04.html").read_text(encoding="utf-8")
    season_05 = (STATIC / "season-05.html").read_text(encoding="utf-8")
    app_source = (ROOT / "web" / "app.py").read_text(encoding="utf-8")

    assert "THE SHADOW" in season_03
    assert "55" in season_03
    assert "65%" in season_03 and "10%" in season_03
    assert "218" in season_03
    assert "titles awarded" in season_03
    assert "Descriptive contrast within one frozen battery" in season_03
    assert 'data-lang="en"' in season_03 and "black-ledger-lang" in season_03

    assert "THE SEASON THE" in season_04
    assert "75%" in season_04 and "0%" in season_04
    assert "960" in season_04
    assert "S04_TERMINATED_HARNESS_POSITIVE" in season_04
    assert "descriptive wrapper contrast" in season_04
    assert 'data-lang="en"' in season_04 and "black-ledger-lang" in season_04

    assert "THE WORD CROSSED" in season_05
    assert "1 / 120" in season_05 and "117 / 120" in season_05
    assert "PREDICTION_PARTIAL" in season_05
    assert "243 / 243" in season_05 and "240 / 240" in season_05
    assert "recorded source" in season_05
    assert "does not establish conscience" in season_05
    assert 'data-lang="en"' in season_05 and "black-ledger-lang" in season_05
    assert "s05-terminal.json" in season_05
    assert "s05-prediction-manifest.json" in season_05

    assert '@app.get("/black-ledger/season-03")' in app_source
    assert '@app.get("/black-ledger/season-04")' in app_source
    assert '@app.get("/black-ledger/season-05")' in app_source

    terminal = (STATIC / "evidence" / "s05-terminal.json").read_text(encoding="utf-8")
    prediction = (STATIC / "evidence" / "s05-prediction-manifest.json").read_text(encoding="utf-8")
    assert '"label":"PREDICTION_PARTIAL"' in terminal
    assert '"terminal_sha256":"b5f87532' in terminal
    assert '"prediction_manifest_sha256":"ffb748c5' in prediction
