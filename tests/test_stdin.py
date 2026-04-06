import json
import pytest
from unittest.mock import patch, MagicMock
from src.cli.stdin import read_stdin_field


def test_stdin_is_tty_returns_empty_list():
    tty_stdin = MagicMock()
    tty_stdin.isatty.return_value = True
    with patch("sys.stdin", tty_stdin):
        result = read_stdin_field("name")
    assert result == []


def test_stdin_ndjson_lines_returns_extracted_field_values():
    lines = [
        json.dumps({"name": "Page A", "uuid": "1"}),
        json.dumps({"name": "Page B", "uuid": "2"}),
    ]
    fake_stdin = MagicMock()
    fake_stdin.isatty.return_value = False
    fake_stdin.__iter__ = MagicMock(return_value=iter(lines))
    with patch("sys.stdin", fake_stdin):
        result = read_stdin_field("name")
    assert result == ["Page A", "Page B"]


def test_stdin_line_missing_field_raises_clear_error():
    lines = [json.dumps({"uuid": "1"})]
    fake_stdin = MagicMock()
    fake_stdin.isatty.return_value = False
    fake_stdin.__iter__ = MagicMock(return_value=iter(lines))
    with patch("sys.stdin", fake_stdin):
        with pytest.raises(ValueError, match="name"):
            read_stdin_field("name")


def test_stdin_multiple_lines_returns_all_values():
    lines = [json.dumps({"uuid": str(i)}) for i in range(5)]
    fake_stdin = MagicMock()
    fake_stdin.isatty.return_value = False
    fake_stdin.__iter__ = MagicMock(return_value=iter(lines))
    with patch("sys.stdin", fake_stdin):
        result = read_stdin_field("uuid")
    assert result == ["0", "1", "2", "3", "4"]
