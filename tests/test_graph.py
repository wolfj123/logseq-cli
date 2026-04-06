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


def test_graph_info_returns_ndjson(runner, mock_service):
    mock_service.get_current_graph.return_value = {
        "name": "my-graph",
        "path": "/home/user/graph",
        "url": "logseq://my-graph",
    }
    result = runner.invoke(app, ["graph", "info"])
    assert result.exit_code == 0
    obj = json.loads(result.stdout.strip())
    assert obj["name"] == "my-graph"
    assert obj["path"] == "/home/user/graph"
