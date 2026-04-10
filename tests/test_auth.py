import json


def test_auth_set_token_stores_profile_and_activates_it(runner, monkeypatch, tmp_path):
    monkeypatch.setenv("LOGSEQ_CLI_CONFIG_DIR", str(tmp_path))

    from src.cli.main import app

    result = runner.invoke(
        app,
        ["auth", "set-token", "token-1234", "--profile", "work"],
    )

    assert result.exit_code == 0
    config = json.loads((tmp_path / "config.json").read_text(encoding="utf-8"))
    assert config["active_profile"] == "work"
    assert config["profiles"]["work"]["token"] == "token-1234"


def test_auth_use_switches_active_profile(runner, monkeypatch, tmp_path):
    monkeypatch.setenv("LOGSEQ_CLI_CONFIG_DIR", str(tmp_path))

    from src.config import set_profile_token
    from src.cli.main import app

    set_profile_token("default", "token-default")
    set_profile_token("work", "token-work", activate=False)

    result = runner.invoke(app, ["auth", "use", "work"])

    assert result.exit_code == 0
    config = json.loads((tmp_path / "config.json").read_text(encoding="utf-8"))
    assert config["active_profile"] == "work"


def test_get_service_uses_stored_active_profile_token(monkeypatch, tmp_path):
    monkeypatch.setenv("LOGSEQ_CLI_CONFIG_DIR", str(tmp_path))
    monkeypatch.delenv("LOGSEQ_TOKEN", raising=False)

    from src.config import set_profile_token
    from src.cli.main import get_service

    set_profile_token("default", "stored-token")
    service = get_service()

    assert service._client._headers["Authorization"] == "Bearer stored-token"


def test_env_token_overrides_stored_profile(monkeypatch, tmp_path):
    monkeypatch.setenv("LOGSEQ_CLI_CONFIG_DIR", str(tmp_path))
    monkeypatch.setenv("LOGSEQ_TOKEN", "env-token")

    from src.config import set_profile_token
    from src.cli.main import get_service

    set_profile_token("default", "stored-token")
    service = get_service()

    assert service._client._headers["Authorization"] == "Bearer env-token"
