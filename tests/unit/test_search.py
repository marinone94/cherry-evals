"""Unit tests for search logic."""

from core.search.hybrid import _reciprocal_rank_fusion


def _make_result(example_id: int, question: str = "Q?") -> dict:
    """Helper to create a result dict for testing."""
    return {
        "id": example_id,
        "dataset_id": 1,
        "dataset_name": "test",
        "question": question,
        "answer": "A",
        "choices": None,
        "example_metadata": None,
        "score": None,
    }


def test_rrf_basic_merge():
    """Test that RRF merges results from both sources."""
    keyword = [_make_result(1), _make_result(2), _make_result(3)]
    semantic = [_make_result(4), _make_result(2), _make_result(5)]

    fused = _reciprocal_rank_fusion(keyword, semantic)

    ids = [r["id"] for r in fused]
    # ID 2 appears in both lists, should be ranked highest
    assert ids[0] == 2
    # All 5 unique results present
    assert len(fused) == 5
    assert set(ids) == {1, 2, 3, 4, 5}


def test_rrf_scores_are_positive():
    """Test that all fused scores are positive."""
    keyword = [_make_result(1), _make_result(2)]
    semantic = [_make_result(3), _make_result(1)]

    fused = _reciprocal_rank_fusion(keyword, semantic)

    for result in fused:
        assert result["score"] > 0


def test_rrf_duplicate_gets_higher_score():
    """Test that a result in both lists gets a higher score than one in only one."""
    keyword = [_make_result(1), _make_result(2)]
    semantic = [_make_result(1), _make_result(3)]

    fused = _reciprocal_rank_fusion(keyword, semantic)

    scores = {r["id"]: r["score"] for r in fused}
    # ID 1 is in both lists, should have higher score than 2 or 3
    assert scores[1] > scores[2]
    assert scores[1] > scores[3]


def test_rrf_respects_weights():
    """Test that weights affect scoring."""
    keyword = [_make_result(1)]
    semantic = [_make_result(2)]

    # Heavy keyword weight
    fused_kw = _reciprocal_rank_fusion(keyword, semantic, keyword_weight=0.9, semantic_weight=0.1)
    scores_kw = {r["id"]: r["score"] for r in fused_kw}

    # Heavy semantic weight
    fused_sem = _reciprocal_rank_fusion(keyword, semantic, keyword_weight=0.1, semantic_weight=0.9)
    scores_sem = {r["id"]: r["score"] for r in fused_sem}

    # With heavy keyword weight, result 1 (from keyword) should score higher
    assert scores_kw[1] > scores_kw[2]
    # With heavy semantic weight, result 2 (from semantic) should score higher
    assert scores_sem[2] > scores_sem[1]


def test_rrf_empty_inputs():
    """Test RRF with empty inputs."""
    assert _reciprocal_rank_fusion([], []) == []
    assert len(_reciprocal_rank_fusion([_make_result(1)], [])) == 1
    assert len(_reciprocal_rank_fusion([], [_make_result(1)])) == 1


def test_rrf_preserves_result_data():
    """Test that RRF preserves the original result data."""
    keyword = [
        {
            "id": 1,
            "dataset_id": 10,
            "dataset_name": "MMLU",
            "question": "What is AI?",
            "answer": "Artificial Intelligence",
            "choices": ["A", "B", "C"],
            "example_metadata": {"subject": "cs"},
            "score": None,
        }
    ]

    fused = _reciprocal_rank_fusion(keyword, [])

    assert fused[0]["question"] == "What is AI?"
    assert fused[0]["answer"] == "Artificial Intelligence"
    assert fused[0]["dataset_name"] == "MMLU"
    assert fused[0]["choices"] == ["A", "B", "C"]
