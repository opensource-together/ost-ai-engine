from src.linker.utils.language_detection import (
    has_non_latin_chars,
    is_blacklisted,
    parse_fasttext_labels,
)


class TestHasNonLatinChars:
    def test_ascii_only(self) -> None:
        assert has_non_latin_chars("hello world") is False

    def test_cjk_characters(self) -> None:
        assert has_non_latin_chars("hello 你好") is True

    def test_arabic_characters(self) -> None:
        assert has_non_latin_chars("مرحبا") is True

    def test_empty_string(self) -> None:
        assert has_non_latin_chars("") is False

    def test_mixed_latin_and_devanagari(self) -> None:
        assert has_non_latin_chars("hello नमस्ते") is True


class TestParseFasttextLabels:
    def test_standard_labels(self) -> None:
        labels = ("__label__en", "__label__fr")
        probs = (0.95, 0.03)
        result = parse_fasttext_labels(labels, probs)
        assert result == [("en", 0.95), ("fr", 0.03)]

    def test_bytes_labels(self) -> None:
        labels = (b"__label__en",)
        probs = (0.9,)
        result = parse_fasttext_labels(labels, probs)
        assert result == [("en", 0.9)]

    def test_empty_inputs(self) -> None:
        result = parse_fasttext_labels((), ())
        assert result == []

    def test_none_inputs(self) -> None:
        result = parse_fasttext_labels(None, None)
        assert result == []

    def test_non_numeric_probability(self) -> None:
        labels = ("__label__en",)
        probs = ("not_a_number",)
        result = parse_fasttext_labels(labels, probs)
        assert result == [("en", 0.0)]


class TestIsBlacklisted:
    def test_no_blacklisted_languages(self) -> None:
        preds = [("en", 0.9), ("fr", 0.05)]
        assert is_blacklisted(preds) is None

    def test_blacklisted_above_threshold(self) -> None:
        preds = [("en", 0.5), ("zh", 0.4)]
        result = is_blacklisted(preds)
        assert result == ("zh", 0.4)

    def test_blacklisted_below_threshold(self) -> None:
        preds = [("en", 0.8), ("ar", 0.1)]
        assert is_blacklisted(preds) is None

    def test_blacklisted_at_threshold(self) -> None:
        preds = [("ru", 0.3)]
        result = is_blacklisted(preds)
        assert result == ("ru", 0.3)

    def test_returns_first_match(self) -> None:
        preds = [("zh", 0.5), ("ar", 0.4)]
        result = is_blacklisted(preds)
        assert result == ("zh", 0.5)
