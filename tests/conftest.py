import pytest
from unittest.mock import AsyncMock, patch
from typer.testing import CliRunner


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_service():
    with patch("src.cli.main.get_service") as mock:
        svc = AsyncMock()
        mock.return_value = svc
        yield svc
