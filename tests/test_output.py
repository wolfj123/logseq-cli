import json
import pytest
from src.cli.output import format_output


def test_single_dict_produces_one_ndjson_line():
    result = format_output({"name": "My Page", "uuid": "abc"})
    lines = result.strip().splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0]) == {"name": "My Page", "uuid": "abc"}


def test_list_of_dicts_produces_one_line_per_item():
    data = [{"name": "A"}, {"name": "B"}, {"name": "C"}]
    result = format_output(data)
    lines = result.strip().splitlines()
    assert len(lines) == 3
    assert [json.loads(l)["name"] for l in lines] == ["A", "B", "C"]


def test_fields_filter_keeps_only_requested_keys():
    data = {"name": "My Page", "uuid": "abc", "isJournal": False}
    result = format_output(data, fields=["name", "uuid"])
    obj = json.loads(result.strip())
    assert obj == {"name": "My Page", "uuid": "abc"}
    assert "isJournal" not in obj


def test_fields_filter_with_missing_key_skips_gracefully():
    data = {"name": "My Page", "uuid": "abc"}
    result = format_output(data, fields=["name", "nonexistent"])
    obj = json.loads(result.strip())
    assert obj == {"name": "My Page"}


def test_plain_produces_human_readable_table():
    data = {"name": "My Page", "uuid": "abc"}
    result = format_output(data, plain=True)
    assert "name" in result
    assert "My Page" in result
    assert "uuid" in result
    assert "abc" in result
    # Not JSON
    try:
        json.loads(result)
        assert False, "Expected non-JSON plain output"
    except (json.JSONDecodeError, ValueError):
        pass
