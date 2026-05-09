import json

from typer.testing import CliRunner


def runner():
    return CliRunner()


def test_auth_set_token_stores_token(monkeypatch, tmp_path):
    monkeypatch.setenv("LOGSEQ_CLI_CONFIG_DIR", str(tmp_path))

    from src.cli.main import app

    result = runner().invoke(app, ["auth", "set-token", "token-1234"])

    assert result.exit_code == 0
    config = json.loads((tmp_path / "config.json").read_text(encoding="utf-8"))
    assert config["token"] == "token-1234"


def test_auth_set_token_overwrites_existing_token(monkeypatch, tmp_path):
    monkeypatch.setenv("LOGSEQ_CLI_CONFIG_DIR", str(tmp_path))

    from src.config import set_token
    from src.cli.main import app

    set_token("old-token")
    result = runner().invoke(app, ["auth", "set-token", "new-token"])

    assert result.exit_code == 0
    config = json.loads((tmp_path / "config.json").read_text(encoding="utf-8"))
    assert config["token"] == "new-token"


def test_auth_set_token_prompts_when_token_argument_omitted(monkeypatch, tmp_path):
    monkeypatch.setenv("LOGSEQ_CLI_CONFIG_DIR", str(tmp_path))

    from src.cli.main import app

    result = runner().invoke(app, ["auth", "set-token"], input="prompt-token\n")

    assert result.exit_code == 0
    config = json.loads((tmp_path / "config.json").read_text(encoding="utf-8"))
    assert config["token"] == "prompt-token"


def test_auth_status_reports_missing_token(monkeypatch, tmp_path):
    monkeypatch.setenv("LOGSEQ_CLI_CONFIG_DIR", str(tmp_path))

    from src.cli.auth import app

    result = runner().invoke(app, ["status"])

    assert result.exit_code == 0
    assert f"Config path: {tmp_path / 'config.json'}" in result.stdout
    assert "Stored token: missing" in result.stdout
    assert "Run `logseq auth set-token` to store a token." in result.stdout


def test_auth_status_masks_stored_token(monkeypatch, tmp_path):
    monkeypatch.setenv("LOGSEQ_CLI_CONFIG_DIR", str(tmp_path))

    from src.config import set_token
    from src.cli.auth import app

    set_token("token-1234")
    result = runner().invoke(app, ["status"])

    assert result.exit_code == 0
    assert f"Config path: {tmp_path / 'config.json'}" in result.stdout
    assert "Stored token: ******1234" in result.stdout


def test_get_service_uses_stored_token(monkeypatch, tmp_path):
    monkeypatch.setenv("LOGSEQ_CLI_CONFIG_DIR", str(tmp_path))
    monkeypatch.delenv("LOGSEQ_TOKEN", raising=False)

    from src.config import set_token
    from src.cli.main import get_service

    set_token("stored-token")
    service = get_service(check_connectivity=False)

    assert service._client._headers["Authorization"] == "Bearer stored-token"


def test_env_token_overrides_stored_token(monkeypatch, tmp_path):
    monkeypatch.setenv("LOGSEQ_CLI_CONFIG_DIR", str(tmp_path))
    monkeypatch.setenv("LOGSEQ_TOKEN", "env-token")

    from src.config import set_token
    from src.cli.main import get_service

    set_token("stored-token")
    service = get_service(check_connectivity=False)

    assert service._client._headers["Authorization"] == "Bearer env-token"


# ---- set-server tests ----

def test_auth_set_server_rejects_empty(monkeypatch, tmp_path):
    monkeypatch.setenv("LOGSEQ_CLI_CONFIG_DIR", str(tmp_path))
    from src.cli.main import app
    result = runner().invoke(app, ["auth", "set-server", ""])
    assert result.exit_code == 2
    assert "cannot be empty" in result.output


def test_auth_set_server_accepts_bare_hostname_no_port(monkeypatch, tmp_path):
    """Bare hostname without port is valid (uses default port 12315)."""
    monkeypatch.setenv("LOGSEQ_CLI_CONFIG_DIR", str(tmp_path))
    from src.cli.main import app
    from unittest.mock import patch
    with patch("src.cli.auth._check_connectivity", return_value=True):
        result = runner().invoke(app, ["auth", "set-server", "127.0.0.1"])
    assert result.exit_code == 0
    assert "Stored Logseq server: http://127.0.0.1:12315/api" in result.stdout


def test_auth_set_server_rejects_port_zero(monkeypatch, tmp_path):
    monkeypatch.setenv("LOGSEQ_CLI_CONFIG_DIR", str(tmp_path))
    from src.cli.main import app
    result = runner().invoke(app, ["auth", "set-server", "127.0.0.1:0"])
    assert result.exit_code == 2
    assert "between" in result.output and "65535" in result.output


def test_auth_set_server_rejects_port_too_large(monkeypatch, tmp_path):
    monkeypatch.setenv("LOGSEQ_CLI_CONFIG_DIR", str(tmp_path))
    from src.cli.main import app
    result = runner().invoke(app, ["auth", "set-server", "127.0.0.1:65536"])
    assert result.exit_code == 2
    assert "between" in result.output and "65535" in result.output


def test_auth_set_server_rejects_non_integer_port(monkeypatch, tmp_path):
    monkeypatch.setenv("LOGSEQ_CLI_CONFIG_DIR", str(tmp_path))
    from src.cli.main import app
    result = runner().invoke(app, ["auth", "set-server", "127.0.0.1:abc"])
    assert result.exit_code == 2
    assert "valid integer" in result.output


def test_auth_set_server_rejects_host_with_spaces(monkeypatch, tmp_path):
    monkeypatch.setenv("LOGSEQ_CLI_CONFIG_DIR", str(tmp_path))
    from src.cli.main import app
    result = runner().invoke(app, ["auth", "set-server", "my host:12315"])
    assert result.exit_code == 2
    assert "must not contain spaces" in result.output


def test_auth_set_server_accepts_valid(monkeypatch, tmp_path):
    monkeypatch.setenv("LOGSEQ_CLI_CONFIG_DIR", str(tmp_path))
    from src.cli.main import app
    from unittest.mock import patch
    with patch("src.cli.auth._check_connectivity", return_value=True):
        result = runner().invoke(app, ["auth", "set-server", "http://10.191.64.81:12315"])
    assert result.exit_code == 0
    assert "Stored Logseq server: http://10.191.64.81:12315/api" in result.stdout
    config = json.loads((tmp_path / "config.json").read_text(encoding="utf-8"))
    assert config["server"] == "http://10.191.64.81:12315/api"
    assert "host" not in config
    assert "port" not in config


def test_auth_set_server_accepts_boundary_ports(monkeypatch, tmp_path):
    monkeypatch.setenv("LOGSEQ_CLI_CONFIG_DIR", str(tmp_path))
    from src.cli.main import app
    from unittest.mock import patch
    with patch("src.cli.auth._check_connectivity", return_value=True):
        r1 = runner().invoke(app, ["auth", "set-server", "http://127.0.0.1:1"])
        assert r1.exit_code == 0
        r2 = runner().invoke(app, ["auth", "set-server", "http://127.0.0.1:65535"])
        assert r2.exit_code == 0


# ---- config layer tests ----

def test_config_set_server_rejects_invalid(monkeypatch, tmp_path):
    monkeypatch.setenv("LOGSEQ_CLI_CONFIG_DIR", str(tmp_path))
    from src.config import set_server
    import pytest
    for val in ["", "127.0.0.1:0", "127.0.0.1:65536", "127.0.0.1:abc", "my host:12315"]:
        with pytest.raises(ValueError):
            set_server(val)


def test_config_set_server_cleans_legacy_keys(monkeypatch, tmp_path):
    monkeypatch.setenv("LOGSEQ_CLI_CONFIG_DIR", str(tmp_path))
    from src.config import set_server, load_config, save_config
    save_config({"host": "old", "port": 9999, "token": "tok"})
    set_server("http://10.0.0.1:8080")
    config = load_config()
    assert config["server"] == "http://10.0.0.1:8080/api"
    assert config["token"] == "tok"


def test_config_load_file_server_defaults(monkeypatch, tmp_path):
    """load_config_file_server() returns None when no config exists."""
    monkeypatch.setenv("LOGSEQ_CLI_CONFIG_DIR", str(tmp_path))
    from src.config import load_config_file_server
    assert load_config_file_server() is None


def test_config_load_file_server_backward_compat(monkeypatch, tmp_path):
    """load_config_file_server() returns None for legacy host/port keys."""
    monkeypatch.setenv("LOGSEQ_CLI_CONFIG_DIR", str(tmp_path))
    from src.config import load_config_file_server, save_config
    save_config({"host": "10.0.0.1", "port": 8080})
    assert load_config_file_server() is None


def test_config_load_file_server_uses_new_key(monkeypatch, tmp_path):
    monkeypatch.setenv("LOGSEQ_CLI_CONFIG_DIR", str(tmp_path))
    from src.config import save_config, load_config_file_server
    save_config({"server": "http://192.168.1.1:9999"})
    assert load_config_file_server() == "http://192.168.1.1:9999"


def test_config_resolve_server_env_overrides_config(monkeypatch, tmp_path):
    monkeypatch.setenv("LOGSEQ_CLI_CONFIG_DIR", str(tmp_path))
    monkeypatch.setenv("LOGSEQ_SERVER", "http://10.0.0.2:5555")
    from src.config import save_config, resolve_server
    save_config({"server": "http://127.0.0.1:12315"})
    url = resolve_server(default="http://fallback:12315")
    assert url == "http://10.0.0.2:5555/api"


def test_config_resolve_server_env_invalid(monkeypatch, tmp_path):
    monkeypatch.setenv("LOGSEQ_CLI_CONFIG_DIR", str(tmp_path))
    monkeypatch.setenv("LOGSEQ_SERVER", "127.0.0.1:abc")
    from src.config import resolve_server
    import pytest
    with pytest.raises(ValueError, match="port is not a valid integer"):
        resolve_server(default="http://fallback:12315")

def test_config_resolve_server_invalid_schema(monkeypatch, tmp_path):
    monkeypatch.setenv("LOGSEQ_CLI_CONFIG_DIR", str(tmp_path))
    monkeypatch.setenv("LOGSEQ_SERVER", "mqtt://127.0.0.1:1883")
    from src.config import resolve_server
    import pytest
    with pytest.raises(ValueError, match="scheme must be http or https"):
        resolve_server(default="http://fallback:12315")

# ---- set-server connectivity prompt tests ----

def test_auth_set_server_prompts_on_connection_failure_and_aborts_on_n(monkeypatch, tmp_path):
    """When connection fails, user declines save (default N)."""
    monkeypatch.setenv("LOGSEQ_CLI_CONFIG_DIR", str(tmp_path))
    from src.cli.main import app
    from unittest.mock import patch
    with patch("src.cli.auth._check_connectivity", return_value=False):
        result = runner().invoke(app, ["auth", "set-server", "127.0.0.1:12315"], input="n\n")
    assert result.exit_code == 0
    assert "Cannot connect to Logseq" in result.output
    assert "not saved" in result.output
    assert not (tmp_path / "config.json").exists()


def test_auth_set_server_prompts_on_connection_failure_and_saves_on_y(monkeypatch, tmp_path):
    """When connection fails, user confirms save (Y)."""
    monkeypatch.setenv("LOGSEQ_CLI_CONFIG_DIR", str(tmp_path))
    from src.cli.main import app
    from unittest.mock import patch
    with patch("src.cli.auth._check_connectivity", return_value=False):
        result = runner().invoke(app, ["auth", "set-server", "127.0.0.1:12315"], input="y\n")
    assert result.exit_code == 0
    assert "Stored Logseq server: http://127.0.0.1:12315/api" in result.stdout
    config = json.loads((tmp_path / "config.json").read_text(encoding="utf-8"))
    assert config["server"] == "http://127.0.0.1:12315/api"


def test_auth_set_server_saves_immediately_when_connected(monkeypatch, tmp_path):
    """When connection succeeds, save happens without prompt."""
    monkeypatch.setenv("LOGSEQ_CLI_CONFIG_DIR", str(tmp_path))
    monkeypatch.setenv("LOGSEQ_TOKEN", "test-token")
    from src.cli.main import app
    from unittest.mock import patch

    with patch("src.cli.auth._check_connectivity", return_value=True):
        with patch("src.cli.auth._get_current_graph", return_value={"name": "Test Graph", "path": "/tmp/test"}):
            result = runner().invoke(app, ["auth", "set-server", "http://127.0.0.1:12315"], input="y\n")

    assert result.exit_code == 0
    assert "Stored Logseq server: http://127.0.0.1:12315/api" in result.stdout
    assert "Connection: OK" in result.stdout
    assert "Current Graph:" in result.stdout
    assert "Test Graph" in result.stdout
    assert "Is this the correct graph?" in result.stdout
    assert "Save this server address anyway" not in result.output
    config = json.loads((tmp_path / "config.json").read_text(encoding="utf-8"))
    assert config["server"] == "http://127.0.0.1:12315/api"


# ---- URL normalizing tests ----

def test_normalize_server_full_url_preserves_port(monkeypatch, tmp_path):
    monkeypatch.setenv("LOGSEQ_CLI_CONFIG_DIR", str(tmp_path))
    from src.config import _normalize_server_url
    assert _normalize_server_url("http://10.191.64.81:12315") == "http://10.191.64.81:12315/api"


def test_normalize_server_http_url_omits_default_port(monkeypatch, tmp_path):
    monkeypatch.setenv("LOGSEQ_CLI_CONFIG_DIR", str(tmp_path))
    from src.config import _normalize_server_url
    assert _normalize_server_url("http://example.com") == "http://example.com/api"


def test_normalize_server_https_url_omits_default_port(monkeypatch, tmp_path):
    monkeypatch.setenv("LOGSEQ_CLI_CONFIG_DIR", str(tmp_path))
    from src.config import _normalize_server_url
    assert _normalize_server_url("https://example.com") == "https://example.com/api"


def test_normalize_server_https_with_explicit_port(monkeypatch, tmp_path):
    monkeypatch.setenv("LOGSEQ_CLI_CONFIG_DIR", str(tmp_path))
    from src.config import _normalize_server_url
    assert _normalize_server_url("https://example.com:8443") == "https://example.com:8443/api"


def test_normalize_server_bare_hostname_adds_scheme_and_port(monkeypatch, tmp_path):
    monkeypatch.setenv("LOGSEQ_CLI_CONFIG_DIR", str(tmp_path))
    from src.config import _normalize_server_url
    assert _normalize_server_url("10.191.64.81") == "http://10.191.64.81:12315/api"


def test_normalize_server_trailing_colon_adds_default_port(monkeypatch, tmp_path):
    monkeypatch.setenv("LOGSEQ_CLI_CONFIG_DIR", str(tmp_path))
    from src.config import _normalize_server_url
    assert _normalize_server_url("10.191.64.81:") == "http://10.191.64.81:12315/api"


def test_normalize_server_empty_raises(monkeypatch, tmp_path):
    monkeypatch.setenv("LOGSEQ_CLI_CONFIG_DIR", str(tmp_path))
    from src.config import _normalize_server_url
    import pytest
    with pytest.raises(ValueError, match="cannot be empty"):
        _normalize_server_url("")


def test_normalize_server_invalid_schema_raises(monkeypatch, tmp_path):
    monkeypatch.setenv("LOGSEQ_CLI_CONFIG_DIR", str(tmp_path))
    from src.config import _normalize_server_url
    import pytest
    with pytest.raises(ValueError, match="scheme must be http or https"):
        _normalize_server_url("mqtt://127.0.0.1:1883")


def test_normalize_server_preserves_explicit_api_path(monkeypatch, tmp_path):
    monkeypatch.setenv("LOGSEQ_CLI_CONFIG_DIR", str(tmp_path))
    from src.config import _normalize_server_url
    assert _normalize_server_url("127.0.0.1/api") == "http://127.0.0.1:12315/api"
    assert _normalize_server_url("http://127.0.0.1:12315/api") == "http://127.0.0.1:12315/api"


def test_normalize_server_preserves_explicit_root_path(monkeypatch, tmp_path):
    monkeypatch.setenv("LOGSEQ_CLI_CONFIG_DIR", str(tmp_path))
    from src.config import _normalize_server_url
    assert _normalize_server_url("http://10.0.0.1:8080/") == "http://10.0.0.1:8080/"


def test_normalize_server_preserves_custom_subpath(monkeypatch, tmp_path):
    monkeypatch.setenv("LOGSEQ_CLI_CONFIG_DIR", str(tmp_path))
    from src.config import _normalize_server_url
    assert _normalize_server_url("https://proxy.com/logseq/api") == "https://proxy.com/logseq/api"


def test_normalize_server_preserves_subpath_without_api(monkeypatch, tmp_path):
    monkeypatch.setenv("LOGSEQ_CLI_CONFIG_DIR", str(tmp_path))
    from src.config import _normalize_server_url
    assert _normalize_server_url("https://proxy.com/logseq") == "https://proxy.com/logseq"


def test_auth_set_server_accepts_full_url(monkeypatch, tmp_path):
    monkeypatch.setenv("LOGSEQ_CLI_CONFIG_DIR", str(tmp_path))
    from src.cli.main import app
    from unittest.mock import patch

    with patch("src.cli.auth._check_connectivity", return_value=True):
        result = runner().invoke(app, ["auth", "set-server", "http://example.com:8080"])

    assert result.exit_code == 0
    assert "Stored Logseq server: http://example.com:8080/api" in result.stdout
    config = json.loads((tmp_path / "config.json").read_text(encoding="utf-8"))
    assert config["server"] == "http://example.com:8080/api"


def test_auth_set_server_accepts_https(monkeypatch, tmp_path):
    monkeypatch.setenv("LOGSEQ_CLI_CONFIG_DIR", str(tmp_path))
    from src.cli.main import app
    from unittest.mock import patch

    with patch("src.cli.auth._check_connectivity", return_value=True):
        result = runner().invoke(app, ["auth", "set-server", "https://example.com"])

    assert result.exit_code == 0
    assert "Stored Logseq server: https://example.com" in result.stdout


def test_config_resolve_server_bare_hostname_env(monkeypatch, tmp_path):
    monkeypatch.setenv("LOGSEQ_CLI_CONFIG_DIR", str(tmp_path))
    monkeypatch.setenv("LOGSEQ_SERVER", "10.0.0.1")
    from src.config import resolve_server
    url = resolve_server(default="http://fallback:12315")
    assert url == "http://10.0.0.1:12315/api"


def test_config_resolve_server_uses_default_when_nothing_configured(monkeypatch, tmp_path):
    """resolve_server uses default as-is when no env var or config exists."""
    monkeypatch.setenv("LOGSEQ_CLI_CONFIG_DIR", str(tmp_path))
    from src.config import resolve_server
    url = resolve_server(default="http://my-default:9999")
    assert url == "http://my-default:9999"


def test_config_resolve_token_env_overrides_config(monkeypatch, tmp_path):
    """LOGSEQ_TOKEN env var overrides config file token."""
    monkeypatch.setenv("LOGSEQ_CLI_CONFIG_DIR", str(tmp_path))
    monkeypatch.setenv("LOGSEQ_TOKEN", "env-token")
    from src.config import set_token, resolve_token
    set_token("config-token")
    assert resolve_token() == "env-token"


def test_config_resolve_token_config_fallback(monkeypatch, tmp_path):
    """When no env var, falls back to config file token."""
    monkeypatch.setenv("LOGSEQ_CLI_CONFIG_DIR", str(tmp_path))
    monkeypatch.delenv("LOGSEQ_TOKEN", raising=False)
    from src.config import set_token, resolve_token
    set_token("config-token")
    assert resolve_token() == "config-token"


def test_config_resolve_token_none(monkeypatch, tmp_path):
    """Returns None when neither env nor config has token."""
    monkeypatch.setenv("LOGSEQ_CLI_CONFIG_DIR", str(tmp_path))
    monkeypatch.delenv("LOGSEQ_TOKEN", raising=False)
    from src.config import resolve_token
    assert resolve_token() is None


def test_auth_set_server_no_token_warns_configure(monkeypatch, tmp_path):
    """When no token, warns user to configure one."""
    monkeypatch.setenv("LOGSEQ_CLI_CONFIG_DIR", str(tmp_path))
    monkeypatch.delenv("LOGSEQ_TOKEN", raising=False)
    from src.cli.main import app
    from unittest.mock import patch
    with patch("src.cli.auth._check_connectivity", return_value=True):
        result = runner().invoke(app, ["auth", "set-server", "http://127.0.0.1:12315"])
    assert result.exit_code == 0
    assert "No token configured" in result.output
    assert "logseq auth set-token" in result.output


def test_auth_set_server_auth_failed_warns_reconfigure(monkeypatch, tmp_path):
    """When token auth fails, warns user to reconfigure."""
    monkeypatch.setenv("LOGSEQ_CLI_CONFIG_DIR", str(tmp_path))
    monkeypatch.setenv("LOGSEQ_TOKEN", "invalid-token")
    from src.cli.main import app
    from src.cli.auth import TokenAuthError
    from unittest.mock import patch
    with patch("src.cli.auth._check_connectivity", return_value=True):
        with patch("src.cli.auth._get_current_graph", side_effect=TokenAuthError("auth failed")):
            result = runner().invoke(app, ["auth", "set-server", "http://127.0.0.1:12315"])
    assert result.exit_code == 0
    assert "Token authentication failed" in result.output
    assert "reconfigure" in result.output


def test_auth_set_server_api_error_shows_generic(monkeypatch, tmp_path):
    """When API error occurs, shows generic warning."""
    monkeypatch.setenv("LOGSEQ_CLI_CONFIG_DIR", str(tmp_path))
    monkeypatch.setenv("LOGSEQ_TOKEN", "test-token")
    from src.cli.main import app
    from src.cli.auth import GraphInfoError
    from unittest.mock import patch
    with patch("src.cli.auth._check_connectivity", return_value=True):
        with patch("src.cli.auth._get_current_graph", side_effect=GraphInfoError("api error")):
            result = runner().invoke(app, ["auth", "set-server", "http://127.0.0.1:12315"])
    assert result.exit_code == 0
    assert "Could not retrieve current graph info" in result.output


def test_config_resolve_server_config_fallback(monkeypatch, tmp_path):
    """When no env var, falls back to config file value."""
    monkeypatch.setenv("LOGSEQ_CLI_CONFIG_DIR", str(tmp_path))
    monkeypatch.delenv("LOGSEQ_SERVER", raising=False)
    from src.config import save_config, resolve_server
    save_config({"server": "http://192.168.1.1:9999/api"})
    url = resolve_server(default="http://fallback:12315")
    assert url == "http://192.168.1.1:9999/api"


def test_config_resolve_server_empty_env_uses_config(monkeypatch, tmp_path):
    """Empty LOGSEQ_SERVER env falls back to config."""
    monkeypatch.setenv("LOGSEQ_CLI_CONFIG_DIR", str(tmp_path))
    monkeypatch.setenv("LOGSEQ_SERVER", "")
    from src.config import save_config, resolve_server
    save_config({"server": "http://127.0.0.1:12315/api"})
    url = resolve_server(default="http://fallback:12315")
    assert url == "http://127.0.0.1:12315/api"


def test_config_resolve_server_env_trims_whitespace(monkeypatch, tmp_path):
    """LOGSEQ_SERVER whitespace is trimmed before normalization."""
    monkeypatch.setenv("LOGSEQ_CLI_CONFIG_DIR", str(tmp_path))
    monkeypatch.setenv("LOGSEQ_SERVER", "  10.0.0.1  ")
    from src.config import resolve_server
    url = resolve_server(default="http://fallback:12315")
    assert url == "http://10.0.0.1:12315/api"


def test_config_resolve_server_default_not_normalized(monkeypatch, tmp_path):
    """Default value is returned as-is without normalization."""
    monkeypatch.setenv("LOGSEQ_CLI_CONFIG_DIR", str(tmp_path))
    monkeypatch.delenv("LOGSEQ_SERVER", raising=False)
    from src.config import resolve_server
    url = resolve_server(default="10.0.0.1:9999")
    assert url == "10.0.0.1:9999"


def test_auth_set_server_shows_graph_info_warning_when_unavailable(monkeypatch, tmp_path):
    """When graph info cannot be retrieved, show a warning."""
    monkeypatch.setenv("LOGSEQ_CLI_CONFIG_DIR", str(tmp_path))
    monkeypatch.setenv("LOGSEQ_TOKEN", "test-token")
    from src.cli.main import app
    from src.cli.auth import GraphInfoError
    from unittest.mock import patch

    with patch("src.cli.auth._check_connectivity", return_value=True):
        with patch("src.cli.auth._get_current_graph", side_effect=GraphInfoError("api error")):
            result = runner().invoke(app, ["auth", "set-server", "http://127.0.0.1:12315"])

    assert result.exit_code == 0
    assert "Stored Logseq server: http://127.0.0.1:12315" in result.stdout
    assert "Connection: OK" in result.stdout
    assert "Could not retrieve current graph info" in result.output


# ---- trim tests ----

def test_auth_set_server_trims_whitespace(monkeypatch, tmp_path):
    """Leading/trailing whitespace should be trimmed from server address."""
    monkeypatch.setenv("LOGSEQ_CLI_CONFIG_DIR", str(tmp_path))
    from src.cli.main import app
    from unittest.mock import patch
    with patch("src.cli.auth._check_connectivity", return_value=True):
        result = runner().invoke(app, ["auth", "set-server", "  http://example.com:8080  "])
    assert result.exit_code == 0
    assert "Stored Logseq server: http://example.com:8080/api" in result.stdout
    config = json.loads((tmp_path / "config.json").read_text(encoding="utf-8"))
    assert config["server"] == "http://example.com:8080/api"


def test_auth_set_server_rejects_whitespace_only(monkeypatch, tmp_path):
    """Whitespace-only input should be rejected as empty."""
    monkeypatch.setenv("LOGSEQ_CLI_CONFIG_DIR", str(tmp_path))
    from src.cli.main import app
    result = runner().invoke(app, ["auth", "set-server", "   "])
    assert result.exit_code == 2
    assert "cannot be empty" in result.output


def test_auth_set_token_trims_whitespace(monkeypatch, tmp_path):
    """Leading/trailing whitespace should be trimmed from token."""
    monkeypatch.setenv("LOGSEQ_CLI_CONFIG_DIR", str(tmp_path))
    from src.cli.main import app
    result = runner().invoke(app, ["auth", "set-token", "  my-token  "])
    assert result.exit_code == 0
    config = json.loads((tmp_path / "config.json").read_text(encoding="utf-8"))
    assert config["token"] == "my-token"

