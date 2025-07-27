from data_ingest.common.chunker import sliding_window_chunks


def test_sliding_window_chunks():
    text = "abcdefghijklmnopqrstuvwxyz" * 10  # 260 chars
    chunks = sliding_window_chunks(text, size=100, overlap_ratio=0.5)
    # Expected: first chunk length 100, step 50 → approx 4-5 chunks
    assert chunks[0] == text[:100]
    assert len(chunks[0]) == 100
    assert len(chunks) >= 4 