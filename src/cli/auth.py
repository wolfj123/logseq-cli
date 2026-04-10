from __future__ import annotations

from typing import Annotated, Optional

import typer

from src.config import get_config_path, get_token, set_token

app = typer.Typer(no_args_is_help=True, help="Manage the stored Logseq API token.")


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
) -> None:
    value = token or typer.prompt("Logseq API token", hide_input=True)
    path = set_token(value)
    typer.echo("Stored Logseq API token")
    typer.echo(f"Config path: {path}")


@app.command("status")
def auth_status() -> None:
    token = get_token()
    typer.echo(f"Config path: {get_config_path()}")
    typer.echo(f"Stored token: {_mask_token(token)}")
    if not token:
        typer.echo("Run `logseq auth set-token` to store a token.")
