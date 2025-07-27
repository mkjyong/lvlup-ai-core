from data_ingest.common.cleaner import clean_text


def test_clean_html_and_whitespace():
    raw = "<p>Hello   World!</p>"  # multiple spaces + HTML
    cleaned = clean_text(raw)
    assert cleaned == "Hello World!" 