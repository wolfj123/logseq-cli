from __future__ import annotations
import typer
from src.cli.output import format_output

app = typer.Typer(no_args_is_help=True)


def _run(coro):
    import asyncio
    return asyncio.run(coro)


def _get_service():
    from src.cli.main import get_service
    return get_service()


@app.command("info")
def graph_info(plain: bool = typer.Option(False, "--plain", help="Human-readable key: value output instead of NDJSON")):
    from src.cli.main import handle_errors

    @handle_errors
    def _run_cmd():
        svc = _get_service()
        info = _run(svc.get_current_graph())
        typer.echo(format_output(info, plain=plain), nl=False)

    _run_cmd()
