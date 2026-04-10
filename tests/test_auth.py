import json


def test_auth_set_token_stores_token(runner, monkeypatch, tmp_path):
    monkeypatch.setenv("LOGSEQ_CLI_CONFIG_DIR", str(tmp_path))

    from src.cli.main import app

    result = runner.invoke(app, ["auth", "set-token", "token-1234"])

    assert result.exit_code == 0
    config = json.loads((tmp_path / "config.json").read_text(encoding="utf-8"))
    assert config["token"] == "token-1234"


def test_auth_set_token_overwrites_existing_token(runner, monkeypatch, tmp_path):
    monkeypatch.setenv("LOGSEQ_CLI_CONFIG_DIR", str(tmp_path))

    from src.config import set_token
    from src.cli.main import app

    set_token("old-token")
    result = runner.invoke(app, ["auth", "set-token", "new-token"])

    assert result.exit_code == 0
    config = json.loads((tmp_path / "config.json").read_text(encoding="utf-8"))
    assert config["token"] == "new-token"


def test_get_service_uses_stored_token(monkeypatch, tmp_path):
    monkeypatch.setenv("LOGSEQ_CLI_CONFIG_DIR", str(tmp_path))
    monkeypatch.delenv("LOGSEQ_TOKEN", raising=False)

    from src.config import set_token
    from src.cli.main import get_service

    set_token("stored-token")
    service = get_service()

    assert service._client._headers["Authorization"] == "Bearer stored-token"


def test_env_token_overrides_stored_token(monkeypatch, tmp_path):
    monkeypatch.setenv("LOGSEQ_CLI_CONFIG_DIR", str(tmp_path))
    monkeypatch.setenv("LOGSEQ_TOKEN", "env-token")

    from src.config import set_token
    from src.cli.main import get_service

    set_token("stored-token")
    service = get_service()

    assert service._client._headers["Authorization"] == "Bearer env-token"
