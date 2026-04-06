from __future__ import annotations

import asyncio
import os
import sys
from typing import Optional

import httpx
import typer
from dotenv import load_dotenv

from src.logseq_client import LogseqClient
from src.logseq_service import LogseqService
from src.cli import page as page_module
from src.cli import block as block_module
from src.cli import graph as graph_module
from src.cli import query as query_module
from src.cli import skill as skill_module

load_dotenv()

app = typer.Typer(no_args_is_help=True)
app.add_typer(page_module.app, name="page")
app.add_typer(block_module.app, name="block")
app.add_typer(graph_module.app, name="graph")
app.add_typer(query_module.app, name="query")
app.add_typer(skill_module.app, name="skill")


def get_service() -> LogseqService:
    token = os.environ.get("LOGSEQ_TOKEN")
    if not token:
        typer.echo("Error: LOGSEQ_TOKEN not set. Add it to .env or export it.", err=True)
        raise typer.Exit(1)
    return LogseqService(LogseqClient(token=token))


def handle_errors(fn):
    """Decorator for subcommand callbacks to catch httpx errors gracefully."""
    import functools

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except httpx.ConnectError:
            typer.echo("Error: Cannot connect to Logseq. Is it running?", err=True)
            raise typer.Exit(1)
        except httpx.HTTPStatusError as e:
            typer.echo(
                f"Error: Logseq API error (status {e.response.status_code}): {e}",
                err=True,
            )
            raise typer.Exit(1)

    return wrapper


if __name__ == "__main__":
    app()
