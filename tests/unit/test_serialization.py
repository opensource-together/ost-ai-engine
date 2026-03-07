import datetime
import uuid

from src.linker.utils.serialization import clean_llm_json, make_serializable


class TestMakeSerializable:
    def test_datetime(self) -> None:
        dt = datetime.datetime(2024, 1, 15, 10, 30, 0)
        assert make_serializable(dt) == "2024-01-15T10:30:00"

    def test_date(self) -> None:
        d = datetime.date(2024, 1, 15)
        assert make_serializable(d) == "2024-01-15"

    def test_uuid(self) -> None:
        u = uuid.UUID("12345678-1234-5678-1234-567812345678")
        assert make_serializable(u) == "12345678-1234-5678-1234-567812345678"

    def test_nested_dict(self) -> None:
        d = datetime.date(2024, 1, 1)
        result = make_serializable({"created": d, "name": "test"})
        assert result == {"created": "2024-01-01", "name": "test"}

    def test_nested_list(self) -> None:
        u = uuid.UUID("12345678-1234-5678-1234-567812345678")
        result = make_serializable([u, "plain"])
        assert result == ["12345678-1234-5678-1234-567812345678", "plain"]

    def test_plain_values_unchanged(self) -> None:
        assert make_serializable(42) == 42
        assert make_serializable("hello") == "hello"
        assert make_serializable(None) is None


class TestCleanLLMJson:
    def test_json_fences(self) -> None:
        raw = '```json\n{"key": "value"}\n```'
        assert clean_llm_json(raw) == '{"key": "value"}'

    def test_plain_fences(self) -> None:
        raw = '```\n{"key": "value"}\n```'
        assert clean_llm_json(raw) == '{"key": "value"}'

    def test_no_fences(self) -> None:
        raw = '{"key": "value"}'
        assert clean_llm_json(raw) == '{"key": "value"}'

    def test_whitespace_around(self) -> None:
        raw = '  ```json\n{"key": "value"}\n```  '
        assert clean_llm_json(raw) == '{"key": "value"}'

    def test_empty_string(self) -> None:
        assert clean_llm_json("") == ""
