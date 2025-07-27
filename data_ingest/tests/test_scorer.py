from data_ingest.common.scorer import compute_score


def test_compute_score_keyword_bias():
    text = "sniper rifle headshot damage increased"
    score_with_kw = compute_score(text, keywords=["sniper", "rifle"])
    score_without_kw = compute_score(text, keywords=["pistol"])
    assert score_with_kw > score_without_kw 