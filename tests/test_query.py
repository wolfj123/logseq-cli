import json
import pytest
from typer.testing import CliRunner
from unittest.mock import AsyncMock, patch
from src.cli.main import app


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_service():
    with patch("src.cli.main.get_service") as mock:
        svc = AsyncMock()
        mock.return_value = svc
        yield svc


def test_query_run_passes_datalog_and_outputs_ndjson(runner, mock_service):
    mock_service.run_query_raw.return_value = [
        ["Page A"], ["Page B"]
    ]
    result = runner.invoke(app, ["query", "run", "[:find ?n :where [?p :block/name ?n]]"])
    assert result.exit_code == 0
    lines = result.stdout.strip().splitlines()
    assert len(lines) == 2
    mock_service.run_query_raw.assert_called_with("[:find ?n :where [?p :block/name ?n]]")


def test_query_run_missing_arg_exits_nonzero(runner, mock_service):
    result = runner.invoke(app, ["query", "run"])
    assert result.exit_code != 0


def test_query_run_defaults_to_all_results(runner, mock_service):
    mock_service.run_query_raw.return_value = [["row"] for _ in range(120)]
    result = runner.invoke(app, ["query", "run", "[:find ?n :where [?p :block/name ?n]]"])
    assert result.exit_code == 0
    assert len(result.stdout.strip().splitlines()) == 120
    mock_service.run_query.assert_not_called()


def test_query_run_page_and_page_size_options(runner, mock_service):
    mock_service.run_query.return_value = {
        "results": [["row1"], ["row2"]],
        "total": 200,
    }
    result = runner.invoke(app, ["query", "run", "[:find ?n]", "--page", "3", "--page-size", "20"])
    assert result.exit_code == 0
    mock_service.run_query.assert_called_with("[:find ?n]", page_number=3, page_size=20)


def test_query_run_with_single_input(runner, mock_service):
    mock_service.run_query_with_inputs.return_value = [["Page A"]]
    result = runner.invoke(app, ["query", "run", "[:find ?n :in $ ?x :where [?p :block/name ?x]]", "--input", "foo"])
    assert result.exit_code == 0
    mock_service.run_query_with_inputs.assert_called_with(
        "[:find ?n :in $ ?x :where [?p :block/name ?x]]", ["foo"]
    )


def test_query_run_with_multiple_inputs(runner, mock_service):
    mock_service.run_query_with_inputs.return_value = [["Page A"]]
    result = runner.invoke(app, ["query", "run", "[:find ?n]", "--input", "foo", "--input", "bar"])
    assert result.exit_code == 0
    mock_service.run_query_with_inputs.assert_called_with("[:find ?n]", ["foo", "bar"])


def test_query_run_has_help(runner):
    result = runner.invoke(app, ["query", "run", "--help"])
    assert result.exit_code == 0
    assert "--input" in result.stdout
    assert "--plain" in result.stdout
    assert "--page" in result.stdout
    assert "Datalog" in result.stdout
