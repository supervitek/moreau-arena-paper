import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "web" / "static"


def test_noir_report_data_is_complete_and_tiered() -> None:
    data = json.loads((STATIC / "noir-track1-report-data.json").read_text(encoding="utf-8"))

    assert data["schemaVersion"] == "moreau-noir-public-track1-report/v1"
    assert data["administrativeStatus"] == (
        "MOREAU_NOIR_TRACK1_CLOSED_WITH_BOUNDED_NULL_PROFILE_ATLAS_AND_ASSAY_LIMIT_MAP"
    )
    assert len(data["systems"]) == 13
    assert len(data["timeline"]) == 17
    assert len(data["sourceDocuments"]) == 7

    panels = [system["panel"] for system in data["systems"]]
    assert panels.count("western") == 7
    assert panels.count("chinese") == 6

    system_ids = [system["id"] for system in data["systems"]]
    assert len(system_ids) == len(set(system_ids))
    assert {system["tier"] for system in data["systems"]} <= set(data["qualificationTiers"])


def test_noir_report_surface_references_its_assets_and_core_result() -> None:
    html = (STATIC / "noir.html").read_text(encoding="utf-8")
    app_source = (ROOT / "web" / "app.py").read_text(encoding="utf-8")

    assert "/static/noir-report.css" in html
    assert "/static/noir-report.js" in html
    assert "+0.48" in html
    assert "415" in html
    assert "−1.44 to +2.51" in html
    assert '@app.get("/noir")' in app_source
