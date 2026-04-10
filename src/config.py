from __future__ import annotations

import json
import os
import platform
from pathlib import Path
from typing import Any


DEFAULT_PROFILE = "default"


def get_config_dir() -> Path:
    override = os.environ.get("LOGSEQ_CLI_CONFIG_DIR")
    if override:
        return Path(override)

    system = platform.system()
    home = Path.home()

    if system == "Windows":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "logseq-cli"
        return home / "AppData" / "Roaming" / "logseq-cli"

    if system == "Darwin":
        return home / "Library" / "Application Support" / "logseq-cli"

    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        return Path(xdg) / "logseq-cli"
    return home / ".config" / "logseq-cli"


def get_config_path() -> Path:
    return get_config_dir() / "config.json"


def load_config() -> dict[str, Any]:
    path = get_config_path()
    if not path.exists():
        return {"active_profile": DEFAULT_PROFILE, "profiles": {}}

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"active_profile": DEFAULT_PROFILE, "profiles": {}}

    if not isinstance(data, dict):
        return {"active_profile": DEFAULT_PROFILE, "profiles": {}}

    profiles = data.get("profiles")
    if not isinstance(profiles, dict):
        profiles = {}

    active_profile = data.get("active_profile")
    if not isinstance(active_profile, str) or not active_profile:
        active_profile = DEFAULT_PROFILE

    return {"active_profile": active_profile, "profiles": profiles}


def save_config(config: dict[str, Any]) -> Path:
    path = get_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def set_profile_token(profile: str, token: str, activate: bool = True) -> Path:
    config = load_config()
    profiles = dict(config.get("profiles", {}))
    entry = dict(profiles.get(profile, {}))
    entry["token"] = token
    profiles[profile] = entry
    config["profiles"] = profiles
    if activate:
        config["active_profile"] = profile
    return save_config(config)


def set_active_profile(profile: str) -> Path:
    config = load_config()
    profiles = config.get("profiles", {})
    if profile not in profiles or not profiles[profile].get("token"):
        raise KeyError(profile)
    config["active_profile"] = profile
    return save_config(config)


def list_profiles() -> list[str]:
    config = load_config()
    profiles = config.get("profiles", {})
    return sorted(name for name, entry in profiles.items() if isinstance(entry, dict) and entry.get("token"))


def get_active_profile() -> str:
    return load_config().get("active_profile", DEFAULT_PROFILE)


def get_profile_token(profile: str) -> str | None:
    config = load_config()
    entry = config.get("profiles", {}).get(profile)
    if not isinstance(entry, dict):
        return None
    token = entry.get("token")
    return token if isinstance(token, str) and token else None


def get_active_profile_token() -> tuple[str, str | None]:
    profile = get_active_profile()
    return profile, get_profile_token(profile)
