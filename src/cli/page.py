from __future__ import annotations

import sys
from typing import Optional

import httpx
import typer

from src.cli.output import format_output
from src.cli.stdin import read_stdin_field

app = typer.Typer(no_args_is_help=True)


def _run(coro):
    import asyncio
    try:
        return asyncio.run(coro)
    except httpx.ConnectError:
        typer.echo("Error: Cannot connect to Logseq. Is it running?", err=True)
        raise typer.Exit(1)
    except httpx.HTTPStatusError as e:
        typer.echo(f"Error: Logseq API error (status {e.response.status_code}): {e}", err=True)
        raise typer.Exit(1)


def _get_service():
    from src.cli.main import get_service
    return get_service()


@app.command("list")
def page_list(
    fields: Optional[str] = typer.Option(None, "--fields", help="Comma-separated fields to include in output. Available: name, uuid, isJournal, properties. E.g. --fields name,uuid"),
    plain: bool = typer.Option(False, "--plain", help="Human-readable key: value output instead of NDJSON"),
    page: Optional[int] = typer.Option(None, "--page", help="Page number for pagination (e.g. --page 1 --page-size 20)"),
    page_size: int = typer.Option(50, "--page-size", help="Number of results per page (used with --page)"),
):
    svc = _get_service()
    if page is not None:
        result = _run(svc.get_all_pages(page_number=page, page_size=page_size))
        pages = result["pages"]
    else:
        raw = _run(svc.get_all_pages_raw())
        pages = [
            {
                "name": p["originalName"],
                "uuid": p["uuid"],
                "properties": p.get("properties"),
                "isJournal": p.get("journal?"),
            }
            for p in raw
        ]
    field_list = [f.strip() for f in fields.split(",")] if fields else None
    typer.echo(format_output(pages, fields=field_list, plain=plain), nl=False)


@app.command("get")
def page_get(
    name: Optional[str] = typer.Argument(None, help="Page name. If omitted, reads .name from piped NDJSON"),
    fields: Optional[str] = typer.Option(None, "--fields", help="Comma-separated fields to include. Available: name, uuid, isJournal, properties. E.g. --fields name,uuid"),
    plain: bool = typer.Option(False, "--plain", help="Human-readable key: value output instead of NDJSON"),
):
    svc = _get_service()
    names = [name] if name else read_stdin_field("name")
    if not names:
        typer.echo("Error: provide a page name or pipe NDJSON with .name", err=True)
        raise typer.Exit(1)
    field_list = [f.strip() for f in fields.split(",")] if fields else None
    for n in names:
        page = _run(svc.get_page_by_name(n))
        if page is None:
            typer.echo(f"Error: page '{n}' not found", err=True)
            raise typer.Exit(1)
        typer.echo(format_output(page, fields=field_list, plain=plain), nl=False)


@app.command("create")
def page_create(
    name: str = typer.Argument(..., help="Name of the page to create"),
    fields: Optional[str] = typer.Option(None, "--fields", help="Comma-separated fields to include in output. Available: name, uuid, isJournal, properties. E.g. --fields name,uuid"),
    plain: bool = typer.Option(False, "--plain", help="Human-readable key: value output instead of NDJSON"),
):
    svc = _get_service()
    page = _run(svc.create_page(name))
    field_list = [f.strip() for f in fields.split(",")] if fields else None
    typer.echo(format_output(page, fields=field_list, plain=plain), nl=False)


@app.command("delete")
def page_delete(
    name: Optional[str] = typer.Argument(None, help="Page name to delete. If omitted, reads .name from piped NDJSON"),
):
    svc = _get_service()
    names = [name] if name else read_stdin_field("name")
    if not names:
        typer.echo("Error: provide a page name or pipe NDJSON with .name", err=True)
        raise typer.Exit(1)
    for n in names:
        _run(svc.delete_page(n))


@app.command("rename")
def page_rename(
    src: str = typer.Argument(..., help="Current page name"),
    dest: str = typer.Argument(..., help="New page name"),
):
    svc = _get_service()
    _run(svc.rename_page(src, dest))


@app.command("refs")
def page_refs(
    name: str = typer.Argument(..., help="Page name to get linked references for"),
    fields: Optional[str] = typer.Option(None, "--fields", help="Comma-separated fields to include in output. E.g. --fields name,uuid"),
    plain: bool = typer.Option(False, "--plain", help="Human-readable key: value output instead of NDJSON"),
):
    svc = _get_service()
    refs = _run(svc.get_page_linked_references(name))
    field_list = [f.strip() for f in fields.split(",")] if fields else None
    typer.echo(format_output(refs, fields=field_list, plain=plain), nl=False)


@app.command("properties")
def page_properties(
    name: str = typer.Argument(..., help="Page name to get properties for"),
    plain: bool = typer.Option(False, "--plain", help="Human-readable key: value output instead of NDJSON"),
):
    """Get page properties from the first block of the page tree."""
    svc = _get_service()
    props = _run(svc.get_page_properties(name))
    typer.echo(format_output(props, plain=plain), nl=False)


@app.command("journal")
def page_journal(
    date: str = typer.Argument(..., help="Date for the journal page in YYYY-MM-DD format. E.g. 2026-03-10"),
    plain: bool = typer.Option(False, "--plain", help="Human-readable key: value output instead of NDJSON"),
):
    """Create or get a journal page using Logseq's YYYY_MM_DD create-page fallback."""
    svc = _get_service()
    try:
        page = _run(svc.create_journal_page(date))
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)
    typer.echo(format_output(page, plain=plain), nl=False)


@app.command("ns-list")
def page_ns_list(
    namespace: str = typer.Argument(..., help="Namespace prefix to list pages under. E.g. 'Projects' lists 'Projects/Alpha', 'Projects/Beta', etc."),
    fields: Optional[str] = typer.Option(None, "--fields", help="Comma-separated fields to include in output. Available: name, uuid, isJournal, properties. E.g. --fields name,uuid"),
    plain: bool = typer.Option(False, "--plain", help="Human-readable key: value output instead of NDJSON"),
):
    """List all pages under a namespace."""
    svc = _get_service()
    pages = _run(svc.get_pages_from_namespace(namespace))
    field_list = [f.strip() for f in fields.split(",")] if fields else None
    typer.echo(format_output(pages, fields=field_list, plain=plain), nl=False)


@app.command("ns-tree")
def page_ns_tree(
    namespace: str = typer.Argument(..., help="Namespace prefix to get the page tree for. E.g. 'Projects'"),
    plain: bool = typer.Option(False, "--plain", help="Human-readable key: value output instead of NDJSON"),
):
    """Get pages under a namespace as a nested tree structure."""
    svc = _get_service()
    tree = _run(svc.get_pages_tree_from_namespace(namespace))
    typer.echo(format_output(tree, plain=plain), nl=False)
