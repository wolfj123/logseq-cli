from __future__ import annotations
from typing import Optional
import httpx
import typer
from src.cli.output import format_output

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


@app.command("run")
def query_run(
    datalog: str = typer.Argument(..., help="Datalog query string to run against the Logseq graph. E.g. '[:find ?name :where [?p :block/original-name ?name]]'"),
    plain: bool = typer.Option(False, "--plain", help="Human-readable key: value output instead of NDJSON"),
    page: Optional[int] = typer.Option(None, "--page", help="Page number for pagination (e.g. --page 1 --page-size 20)"),
    page_size: int = typer.Option(50, "--page-size", help="Number of results per page (used with --page)"),
    input: Optional[list[str]] = typer.Option(None, "--input", help="Input value for a parameterized query. Repeat for multiple inputs. E.g. --input foo --input bar"),
):
    svc = _get_service()
    if input:
        rows = _run(svc.run_query_with_inputs(datalog, input))
    elif page is not None:
        result = _run(svc.run_query(datalog, page_number=page, page_size=page_size))
        rows = result["results"]
    else:
        rows = _run(svc.run_query_raw(datalog))
    typer.echo(format_output(rows, plain=plain), nl=False)
