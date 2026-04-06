from __future__ import annotations
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


@app.command("get")
def block_get(
    uuid: Optional[str] = typer.Argument(None, help="Block UUID. If omitted, reads .uuid from piped NDJSON"),
    fields: Optional[str] = typer.Option(None, "--fields", help="Comma-separated fields to include in output. Available: uuid, content, page, properties. E.g. --fields uuid,content"),
    include_children: bool = typer.Option(False, "--include-children", help="Include nested child blocks in the response"),
    plain: bool = typer.Option(False, "--plain", help="Human-readable key: value output instead of NDJSON"),
):
    svc = _get_service()
    uuids = [uuid] if uuid else read_stdin_field("uuid")
    if not uuids:
        typer.echo("Error: provide a uuid or pipe NDJSON with .uuid", err=True)
        raise typer.Exit(1)
    field_list = [f.strip() for f in fields.split(",")] if fields else None
    for u in uuids:
        block = _run(svc.get_block_by_uuid(u, include_children=include_children))
        typer.echo(format_output(block, fields=field_list, plain=plain), nl=False)


@app.command("insert")
def block_insert(
    content: str = typer.Argument(..., help="Content of the new block"),
    uuid: Optional[str] = typer.Option(None, "--uuid", help="Reference block UUID. If omitted, reads .uuid from piped NDJSON"),
    sibling: bool = typer.Option(False, "--sibling", help="Insert as a sibling of the reference block (same level). Default: insert as a child (indented under it)"),
    plain: bool = typer.Option(False, "--plain", help="Human-readable key: value output instead of NDJSON"),
):
    """Insert a block relative to a reference block. By default inserts as a child (indented). Use --sibling to insert at the same level."""
    svc = _get_service()
    uuids = [uuid] if uuid else read_stdin_field("uuid")
    if not uuids:
        typer.echo("Error: provide --uuid or pipe NDJSON with .uuid", err=True)
        raise typer.Exit(1)
    for u in uuids:
        block = _run(svc.insert_block(u, content, opts={"sibling": sibling}))
        typer.echo(format_output(block, plain=plain), nl=False)


@app.command("update")
def block_update(
    uuid: str = typer.Argument(..., help="UUID of the block to update"),
    content: str = typer.Argument(..., help="New content for the block"),
    plain: bool = typer.Option(False, "--plain", help="Human-readable key: value output instead of NDJSON"),
):
    svc = _get_service()
    block = _run(svc.update_block(uuid, content))
    typer.echo(format_output(block, plain=plain), nl=False)


@app.command("remove")
def block_remove(
    uuid: Optional[str] = typer.Argument(None, help="Block UUID to remove. If omitted, reads .uuid from piped NDJSON"),
):
    svc = _get_service()
    uuids = [uuid] if uuid else read_stdin_field("uuid")
    if not uuids:
        typer.echo("Error: provide a uuid or pipe NDJSON with .uuid", err=True)
        raise typer.Exit(1)
    for u in uuids:
        _run(svc.remove_block(u))


@app.command("prepend")
def block_prepend(
    page: str = typer.Argument(..., help="Page name to prepend the block to"),
    content: str = typer.Argument(..., help="Content of the new block"),
    plain: bool = typer.Option(False, "--plain", help="Human-readable key: value output instead of NDJSON"),
):
    svc = _get_service()
    block = _run(svc.prepend_block_in_page(page, content))
    typer.echo(format_output(block, plain=plain), nl=False)


@app.command("append")
def block_append(
    page: str = typer.Argument(..., help="Page name to append the block to"),
    content: str = typer.Argument(..., help="Content of the new block"),
    plain: bool = typer.Option(False, "--plain", help="Human-readable key: value output instead of NDJSON"),
):
    svc = _get_service()
    block = _run(svc.append_block_in_page(page, content))
    typer.echo(format_output(block, plain=plain), nl=False)


@app.command("move")
def block_move(
    src_uuid: str = typer.Argument(..., help="UUID of the block to move"),
    target_uuid: str = typer.Argument(..., help="UUID of the target reference block"),
    sibling: bool = typer.Option(False, "--sibling", help="Move as a sibling of the target (same level). Default: move as a child (indented under it)"),
    plain: bool = typer.Option(False, "--plain", help="Human-readable key: value output instead of NDJSON"),
):
    """Move a block to a new position. By default places it as a child of the target. Use --sibling to place at the same level."""
    svc = _get_service()
    result = _run(svc.move_block(src_uuid, target_uuid, opts={"before": False, "children": not sibling}))
    typer.echo(format_output(result, plain=plain), nl=False)


@app.command("collapse")
def block_collapse(
    uuid: str = typer.Argument(..., help="UUID of the block to collapse or expand"),
    expand: bool = typer.Option(False, "--expand", help="Expand the block instead of collapsing it"),
    toggle: bool = typer.Option(False, "--toggle", help="Toggle collapsed state"),
):
    """Collapse a block. Use --expand to expand or --toggle to switch state."""
    svc = _get_service()
    if toggle:
        flag = "toggle"
    elif expand:
        flag = False
    else:
        flag = True
    _run(svc.set_block_collapsed(uuid, flag))


@app.command("properties")
def block_properties(
    uuid: str = typer.Argument(..., help="UUID of the block to get properties for"),
    plain: bool = typer.Option(False, "--plain", help="Human-readable key: value output instead of NDJSON"),
):
    svc = _get_service()
    props = _run(svc.get_block_properties(uuid))
    typer.echo(format_output(props, plain=plain), nl=False)


@app.command("prop-set")
def block_prop_set(
    uuid: str = typer.Argument(..., help="UUID of the block"),
    key: str = typer.Argument(..., help="Property key to set"),
    value: str = typer.Argument(..., help="Property value"),
):
    """Set or update a property on a block."""
    svc = _get_service()
    _run(svc.upsert_block_property(uuid, key, value))


@app.command("prop-remove")
def block_prop_remove(
    uuid: str = typer.Argument(..., help="UUID of the block"),
    key: str = typer.Argument(..., help="Property key to remove"),
):
    """Remove a property from a block."""
    svc = _get_service()
    _run(svc.remove_block_property(uuid, key))


@app.command("insert-batch")
def block_insert_batch(
    uuid: str = typer.Argument(..., help="UUID of the reference block to insert after"),
    batch_json: str = typer.Argument(..., help='JSON array of block objects with "content" and optional "children". E.g. \'[{"content": "Block 1"}, {"content": "Block 2", "children": [{"content": "Child"}]}]\''),
    sibling: bool = typer.Option(False, "--sibling", help="Insert blocks as siblings of the reference block. Default: insert as children"),
    plain: bool = typer.Option(False, "--plain", help="Human-readable key: value output instead of NDJSON"),
):
    """Insert multiple blocks with optional hierarchy in a single call."""
    import json
    try:
        batch = json.loads(batch_json)
    except json.JSONDecodeError as e:
        typer.echo(f"Error: invalid JSON: {e}", err=True)
        raise typer.Exit(1)
    svc = _get_service()
    result = _run(svc.insert_batch_block(uuid, batch, opts={"sibling": sibling}))
    typer.echo(format_output(result, plain=plain), nl=False)
