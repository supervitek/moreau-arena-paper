from web.app import _fight_s1_logic, _normalize_s1_stats


def test_normalize_s1_stats_preserves_budget_and_shape() -> None:
    normalized = _normalize_s1_stats(13, 15, 14, 14)

    assert sum(normalized) == 24
    assert all(stat >= 1 for stat in normalized)
    assert normalized[1] >= normalized[0]
    assert normalized[2] >= normalized[0]


def test_fight_s1_logic_accepts_extended_island_stats() -> None:
    result = _fight_s1_logic("panther 13 15 14 14", "fox 4 7 7 2", 1, seed=7)

    assert result.build1_wins + result.build2_wins + result.draws == 1
    assert result.avg_ticks >= 0
