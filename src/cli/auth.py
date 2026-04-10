from __future__ import annotations

from typing import Annotated, Optional

import typer

from src.config import (
    DEFAULT_PROFILE,
    get_active_profile,
    get_config_path,
    get_profile_token,
    list_profiles,
    set_active_profile,
    set_profile_token,
)

app = typer.Typer(no_args_is_help=True, help="Manage stored Logseq API tokens.")


def _mask_token(token: str | None) -> str:
    if not token:
        return "missing"
    if len(token) <= 4:
        return "*" * len(token)
    return "*" * (len(token) - 4) + token[-4:]


@app.command("set-token")
def auth_set_token(
    token: Annotated[
        Optional[str],
        typer.Argument(help="Logseq API token. If omitted, you will be prompted securely."),
    ] = None,
    profile: Annotated[
        str,
        typer.Option(help="Profile name to store the token under."),
    ] = DEFAULT_PROFILE,
    activate: Annotated[
        bool,
        typer.Option("--activate/--no-activate", help="Set this profile as the active profile after saving."),
    ] = True,
) -> None:
    value = token or typer.prompt("Logseq API token", hide_input=True)
    path = set_profile_token(profile=profile, token=value, activate=activate)
    typer.echo(f"Stored token for profile: {profile}")
    if activate:
        typer.echo(f"Active profile: {profile}")
    typer.echo(f"Config path: {path}")


@app.command("use")
def auth_use(
    profile: Annotated[str, typer.Argument(help="Stored profile name to activate.")],
) -> None:
    try:
        path = set_active_profile(profile)
    except KeyError:
        typer.echo(f"Error: profile '{profile}' does not exist or has no token.", err=True)
        typer.echo("Run `logseq auth set-token --profile <name>` first.", err=True)
        raise typer.Exit(1)

    typer.echo(f"Active profile: {profile}")
    typer.echo(f"Config path: {path}")


@app.command("status")
def auth_status() -> None:
    active_profile = get_active_profile()
    active_token = get_profile_token(active_profile)
    profiles = list_profiles()

    typer.echo(f"Config path: {get_config_path()}")
    typer.echo(f"Active profile: {active_profile}")
    typer.echo(f"Active token: {_mask_token(active_token)}")

    if not profiles:
        typer.echo("Stored profiles: none")
        typer.echo("Run `logseq auth set-token` to store a token.")
        return

    typer.echo("Stored profiles:")
    for profile in profiles:
        marker = "*" if profile == active_profile else "-"
        typer.echo(f"{marker} {profile}")
