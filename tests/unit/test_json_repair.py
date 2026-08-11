import pytest
from openstory.services.json_repair import StructuredOutputError, extract_json_value


def test_extract_json_value_parses_complete_json() -> None:
    assert extract_json_value('{"name": "Lira", "active": true}') == {
        "name": "Lira",
        "active": True,
    }


def test_extract_json_value_parses_fenced_json() -> None:
    assert extract_json_value('```json\n{"entities": []}\n```') == {"entities": []}


def test_extract_json_value_finds_balanced_json_inside_prose() -> None:
    text = 'Result follows: {"note": "a } brace and \\"quote\\"", "items": [1, 2]} Thanks.'

    assert extract_json_value(text) == {
        "note": 'a } brace and "quote"',
        "items": [1, 2],
    }


def test_extract_json_value_supports_top_level_arrays() -> None:
    assert extract_json_value("Answer: [1, {\"nested\": true}] end") == [
        1,
        {"nested": True},
    ]


def test_structured_output_error_limits_diagnostic_preview() -> None:
    secret_tail = "DO_NOT_INCLUDE_THIS_TAIL"
    invalid = "x" * 500 + secret_tail

    with pytest.raises(StructuredOutputError) as captured:
        extract_json_value(invalid)

    assert secret_tail not in str(captured.value)
    assert len(captured.value.preview) <= 200
