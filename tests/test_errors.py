import json
import pytest
from typer.testing import CliRunner
from unittest.mock import AsyncMock, patch, MagicMock
import httpx
from src.cli.main import app


@pytest.fixture
def runner():
    return CliRunner()


def test_missing_token_exits_1_with_clear_message(runner):
    with patch.dict("os.environ", {}, clear=True):
        # Ensure LOGSEQ_TOKEN is not set
        import os
        os.environ.pop("LOGSEQ_TOKEN", None)
        result = runner.invoke(app, ["graph", "info"])
    assert result.exit_code == 1
    assert "LOGSEQ_TOKEN" in result.stderr


def test_connect_error_prints_friendly_message(runner):
    with patch("src.cli.main.get_service") as mock:
        svc = AsyncMock()
        svc.get_current_graph.side_effect = httpx.ConnectError("refused")
        mock.return_value = svc
        result = runner.invoke(app, ["graph", "info"])
    assert result.exit_code == 1
    assert "Cannot connect to Logseq" in result.stderr


def test_http_status_error_shows_status_code(runner):
    with patch("src.cli.main.get_service") as mock:
        svc = AsyncMock()
        response = MagicMock()
        response.status_code = 401
        svc.get_current_graph.side_effect = httpx.HTTPStatusError(
            "Unauthorized", request=MagicMock(), response=response
        )
        mock.return_value = svc
        result = runner.invoke(app, ["graph", "info"])
    assert result.exit_code == 1
    assert "401" in result.stderr


def test_error_goes_to_stderr_stdout_stays_clean(runner):
    with patch("src.cli.main.get_service") as mock:
        svc = AsyncMock()
        svc.get_current_graph.side_effect = httpx.ConnectError("refused")
        mock.return_value = svc
        result = runner.invoke(app, ["graph", "info"])
    assert result.stdout == ""
    assert result.exit_code == 1


def test_missing_required_arg_exits_nonzero(runner):
    with patch("src.cli.main.get_service") as mock:
        mock.return_value = AsyncMock()
        result = runner.invoke(app, ["block", "update"])
    assert result.exit_code != 0
