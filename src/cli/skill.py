from __future__ import annotations

import re
from importlib import resources
from pathlib import Path
from typing import Annotated

import typer

from src import __version__

app = typer.Typer(no_args_is_help=True, help="Manage agent skill installation.")

SKILL_NAME = "logseq-cli"
VERSION_PATTERN = re.compile(r"logseq-cli v([\d.]+)")
TARGETS = {
    "claude": (".claude", "Claude Code"),
    "agents": (".agents", "Agent Skills"),
}


def get_scope_root(scope: str) -> Path:
    return Path.home() if scope == "user" else Path.cwd()


def iter_targets(target: str) -> list[str]:
    return list(TARGETS) if target == "all" else [target]


def get_skill_path(target: str, scope: str) -> Path:
    root_dir, _label = TARGETS[target]
    return get_scope_root(scope) / root_dir / "skills" / SKILL_NAME / "SKILL.md"


def get_skill_source_content() -> str | None:
    repo_skill = Path(__file__).resolve().parents[2] / "SKILL.md"
    if repo_skill.exists():
        return repo_skill.read_text(encoding="utf-8")

    try:
        return (resources.files("src") / "data" / "SKILL.md").read_text(encoding="utf-8")
    except (FileNotFoundError, ModuleNotFoundError, TypeError):
        return None


def add_version_comment(content: str, version: str) -> str:
    version_comment = f"<!-- logseq-cli v{version} -->\n"
    if "---" in content:
        parts = content.split("---", 2)
        if len(parts) >= 3:
            return f"---{parts[1]}---\n{version_comment}{parts[2].lstrip()}"
    return version_comment + content


def get_skill_version(skill_path: Path) -> str | None:
    if not skill_path.exists():
        return None
    content = skill_path.read_text(encoding="utf-8")[:500]
    match = VERSION_PATTERN.search(content)
    return match.group(1) if match else None


def remove_empty_parents(skill_path: Path, scope: str) -> None:
    current = skill_path.parent
    stop_at = get_scope_root(scope)
    while current != stop_at:
        try:
            current.rmdir()
        except OSError:
            break
        current = current.parent


def get_installed_content(target: str, scope: str) -> str | None:
    skill_path = get_skill_path(target, scope)
    if not skill_path.exists():
        return None
    return skill_path.read_text(encoding="utf-8")


@app.command("install")
def install_skill(
    scope: Annotated[
        str,
        typer.Option(help="Install for the current user or the current project."),
    ] = "user",
    target: Annotated[
        str,
        typer.Option(help="Install into Claude Code, .agents, or both."),
    ] = "all",
) -> None:
    content = get_skill_source_content()
    if content is None:
        typer.echo("Error: Skill source not found in package data.", err=True)
        raise typer.Exit(1)

    stamped_content = add_version_comment(content, __version__)
    installed_paths: list[tuple[str, Path]] = []
    failed_targets: list[tuple[str, OSError]] = []

    for target_name in iter_targets(target):
        skill_path = get_skill_path(target_name, scope)
        try:
            skill_path.parent.mkdir(parents=True, exist_ok=True)
            skill_path.write_text(stamped_content, encoding="utf-8")
            installed_paths.append((target_name, skill_path))
        except OSError as exc:
            failed_targets.append((target_name, exc))

    if installed_paths:
        typer.echo("Installed logseq-cli skill")
        typer.echo(f"Version: {__version__}")
        typer.echo(f"Scope: {scope}")
        for target_name, skill_path in installed_paths:
            typer.echo(f"{TARGETS[target_name][1]}: {skill_path}")

    for target_name, exc in failed_targets:
        typer.echo(f"Failed to install {TARGETS[target_name][1]}: {exc}", err=True)

    if failed_targets:
        raise typer.Exit(1)


@app.command("status")
def skill_status(
    scope: Annotated[
        str,
        typer.Option(help="Inspect user-level or project-level skill installs."),
    ] = "user",
    target: Annotated[
        str,
        typer.Option(help="Inspect Claude Code, .agents, or both."),
    ] = "all",
) -> None:
    installed_any = False
    typer.echo(f"logseq-cli skill status ({scope} scope)")
    typer.echo(f"CLI version: {__version__}")

    for target_name in iter_targets(target):
        skill_path = get_skill_path(target_name, scope)
        skill_version = get_skill_version(skill_path)
        status_text = "Installed" if skill_path.exists() else "Not installed"
        typer.echo(f"{TARGETS[target_name][1]}: {status_text}")
        typer.echo(f"Path: {skill_path}")
        if skill_path.exists():
            installed_any = True
            typer.echo(f"Skill version: {skill_version or 'unknown'}")
            if skill_version and skill_version != __version__:
                typer.echo("Version mismatch - run `logseq skill install`")

    if not installed_any:
        typer.echo("Run `logseq skill install` to install the skill.")


@app.command("uninstall")
def uninstall_skill(
    scope: Annotated[
        str,
        typer.Option(help="Remove user-level or project-level skill installs."),
    ] = "user",
    target: Annotated[
        str,
        typer.Option(help="Remove Claude Code, .agents, or both."),
    ] = "all",
) -> None:
    removed_targets: list[str] = []
    for target_name in iter_targets(target):
        skill_path = get_skill_path(target_name, scope)
        if not skill_path.exists():
            continue
        skill_path.unlink()
        remove_empty_parents(skill_path, scope)
        removed_targets.append(target_name)

    if not removed_targets:
        typer.echo("Skill not installed")
        return

    typer.echo("Uninstalled logseq-cli skill")
    for target_name in removed_targets:
        typer.echo(f"Removed from {TARGETS[target_name][1]}")


@app.command("show")
def show_skill(
    scope: Annotated[
        str,
        typer.Option(help="Read an installed skill from user or project scope."),
    ] = "user",
    target: Annotated[
        str,
        typer.Option(help="Show the packaged skill source or an installed target."),
    ] = "source",
) -> None:
    if target == "source":
        content = get_skill_source_content()
        if content is None:
            typer.echo("Error: Skill source not found in package data.", err=True)
            raise typer.Exit(1)
        typer.echo(content)
        return

    content = get_installed_content(target, scope)
    if content is None:
        typer.echo("Skill not installed")
        typer.echo("Run `logseq skill install` first.")
        return

    typer.echo(content)
