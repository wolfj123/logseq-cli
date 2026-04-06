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


# --- block get ---

def test_block_get_returns_ndjson(runner, mock_service):
    mock_service.get_block_by_uuid.return_value = {"uuid": "abc", "content": "Hello"}
    result = runner.invoke(app, ["block", "get", "abc"])
    assert result.exit_code == 0
    assert json.loads(result.stdout.strip())["uuid"] == "abc"


def test_block_get_reads_uuid_from_stdin(runner, mock_service):
    mock_service.get_block_by_uuid.return_value = {"uuid": "abc", "content": "Hi"}
    stdin = json.dumps({"uuid": "abc"}) + "\n"
    result = runner.invoke(app, ["block", "get"], input=stdin)
    assert result.exit_code == 0
    mock_service.get_block_by_uuid.assert_called_with("abc", include_children=False)


def test_block_get_include_children(runner, mock_service):
    mock_service.get_block_by_uuid.return_value = {"uuid": "abc", "content": "Hi", "children": []}
    result = runner.invoke(app, ["block", "get", "abc", "--include-children"])
    assert result.exit_code == 0
    mock_service.get_block_by_uuid.assert_called_with("abc", include_children=True)


# --- block insert ---

def test_block_insert_calls_insert_and_prints(runner, mock_service):
    mock_service.insert_block.return_value = {"uuid": "new", "content": "content"}
    result = runner.invoke(app, ["block", "insert", "content", "--uuid", "parent-uuid"])
    assert result.exit_code == 0
    mock_service.insert_block.assert_called_with("parent-uuid", "content", opts={"sibling": False})
    assert json.loads(result.stdout.strip())["uuid"] == "new"


def test_block_insert_reads_uuid_from_stdin(runner, mock_service):
    mock_service.insert_block.return_value = {"uuid": "new", "content": "hi"}
    stdin = json.dumps({"uuid": "parent-uuid"}) + "\n"
    result = runner.invoke(app, ["block", "insert", "hi"], input=stdin)
    assert result.exit_code == 0
    mock_service.insert_block.assert_called_with("parent-uuid", "hi", opts={"sibling": False})


def test_block_insert_sibling_flag(runner, mock_service):
    mock_service.insert_block.return_value = {"uuid": "new", "content": "hi"}
    result = runner.invoke(app, ["block", "insert", "hi", "--uuid", "parent-uuid", "--sibling"])
    assert result.exit_code == 0
    mock_service.insert_block.assert_called_with("parent-uuid", "hi", opts={"sibling": True})


# --- block update ---

def test_block_update_calls_update_block(runner, mock_service):
    mock_service.update_block.return_value = {"uuid": "abc", "content": "new content"}
    result = runner.invoke(app, ["block", "update", "abc", "new content"])
    assert result.exit_code == 0
    mock_service.update_block.assert_called_with("abc", "new content")


# --- block remove ---

def test_block_remove_exits_0(runner, mock_service):
    mock_service.remove_block.return_value = None
    result = runner.invoke(app, ["block", "remove", "abc"])
    assert result.exit_code == 0
    mock_service.remove_block.assert_called_with("abc")


def test_block_remove_reads_uuid_from_stdin(runner, mock_service):
    mock_service.remove_block.return_value = None
    stdin = json.dumps({"uuid": "abc"}) + "\n"
    result = runner.invoke(app, ["block", "remove"], input=stdin)
    assert result.exit_code == 0
    mock_service.remove_block.assert_called_with("abc")


# --- block prepend ---

def test_block_prepend_calls_prepend_block_in_page(runner, mock_service):
    mock_service.prepend_block_in_page.return_value = {"uuid": "new", "content": "prepended"}
    result = runner.invoke(app, ["block", "prepend", "My Page", "prepended"])
    assert result.exit_code == 0
    mock_service.prepend_block_in_page.assert_called_with("My Page", "prepended")


# --- block append ---

def test_block_append_calls_append_block_in_page(runner, mock_service):
    mock_service.append_block_in_page.return_value = {"uuid": "new", "content": "appended"}
    result = runner.invoke(app, ["block", "append", "My Page", "appended"])
    assert result.exit_code == 0
    mock_service.append_block_in_page.assert_called_with("My Page", "appended")


# --- block properties ---

def test_block_properties_returns_ndjson(runner, mock_service):
    mock_service.get_block_properties.return_value = {"key": "value"}
    result = runner.invoke(app, ["block", "properties", "abc"])
    assert result.exit_code == 0
    assert json.loads(result.stdout.strip())["key"] == "value"


# --- block move ---

def test_block_move_as_child_by_default(runner, mock_service):
    mock_service.move_block.return_value = {"uuid": "src"}
    result = runner.invoke(app, ["block", "move", "src-uuid", "target-uuid"])
    assert result.exit_code == 0
    mock_service.move_block.assert_called_with("src-uuid", "target-uuid", opts={"before": False, "children": True})


def test_block_move_as_sibling(runner, mock_service):
    mock_service.move_block.return_value = {"uuid": "src"}
    result = runner.invoke(app, ["block", "move", "src-uuid", "target-uuid", "--sibling"])
    assert result.exit_code == 0
    mock_service.move_block.assert_called_with("src-uuid", "target-uuid", opts={"before": False, "children": False})


# --- block collapse ---

def test_block_collapse_collapses_by_default(runner, mock_service):
    mock_service.set_block_collapsed.return_value = None
    result = runner.invoke(app, ["block", "collapse", "abc"])
    assert result.exit_code == 0
    mock_service.set_block_collapsed.assert_called_with("abc", True)


def test_block_collapse_expand_flag(runner, mock_service):
    mock_service.set_block_collapsed.return_value = None
    result = runner.invoke(app, ["block", "collapse", "abc", "--expand"])
    assert result.exit_code == 0
    mock_service.set_block_collapsed.assert_called_with("abc", False)


def test_block_collapse_toggle_flag(runner, mock_service):
    mock_service.set_block_collapsed.return_value = None
    result = runner.invoke(app, ["block", "collapse", "abc", "--toggle"])
    assert result.exit_code == 0
    mock_service.set_block_collapsed.assert_called_with("abc", "toggle")


# --- block prop-set ---

def test_block_prop_set_calls_upsert(runner, mock_service):
    mock_service.upsert_block_property.return_value = None
    result = runner.invoke(app, ["block", "prop-set", "abc", "type", "note"])
    assert result.exit_code == 0
    mock_service.upsert_block_property.assert_called_with("abc", "type", "note")


# --- block prop-remove ---

def test_block_prop_remove_calls_remove(runner, mock_service):
    mock_service.remove_block_property.return_value = None
    result = runner.invoke(app, ["block", "prop-remove", "abc", "type"])
    assert result.exit_code == 0
    mock_service.remove_block_property.assert_called_with("abc", "type")


# --- block insert-batch ---

def test_block_insert_batch_calls_insert_batch(runner, mock_service):
    mock_service.insert_batch_block.return_value = [{"uuid": "b1"}, {"uuid": "b2"}]
    batch = '[{"content": "Block 1"}, {"content": "Block 2"}]'
    result = runner.invoke(app, ["block", "insert-batch", "parent-uuid", batch])
    assert result.exit_code == 0
    mock_service.insert_batch_block.assert_called_with(
        "parent-uuid",
        [{"content": "Block 1"}, {"content": "Block 2"}],
        opts={"sibling": False},
    )


def test_block_insert_batch_invalid_json_exits_1(runner, mock_service):
    result = runner.invoke(app, ["block", "insert-batch", "parent-uuid", "not-json"])
    assert result.exit_code == 1


# --- help text coverage ---

def test_block_get_has_help(runner):
    result = runner.invoke(app, ["block", "get", "--help"])
    assert result.exit_code == 0
    assert "--fields" in result.stdout
    assert "--include-children" in result.stdout
    assert "--plain" in result.stdout


def test_block_insert_has_help(runner):
    result = runner.invoke(app, ["block", "insert", "--help"])
    assert result.exit_code == 0
    assert "--uuid" in result.stdout
    assert "--sibling" in result.stdout
    assert "--plain" in result.stdout


def test_block_append_has_help(runner):
    result = runner.invoke(app, ["block", "append", "--help"])
    assert result.exit_code == 0
    assert "--plain" in result.stdout


def test_block_move_has_help(runner):
    result = runner.invoke(app, ["block", "move", "--help"])
    assert result.exit_code == 0
    assert "--sibling" in result.stdout


def test_block_collapse_has_help(runner):
    result = runner.invoke(app, ["block", "collapse", "--help"])
    assert result.exit_code == 0
    assert "--expand" in result.stdout
    assert "--toggle" in result.stdout


def test_block_prop_set_has_help(runner):
    result = runner.invoke(app, ["block", "prop-set", "--help"])
    assert result.exit_code == 0
    assert "key" in result.stdout.lower() or "KEY" in result.stdout


def test_block_prop_remove_has_help(runner):
    result = runner.invoke(app, ["block", "prop-remove", "--help"])
    assert result.exit_code == 0
    assert "key" in result.stdout.lower() or "KEY" in result.stdout


def test_block_insert_batch_has_help(runner):
    result = runner.invoke(app, ["block", "insert-batch", "--help"])
    assert result.exit_code == 0
    assert "--sibling" in result.stdout
