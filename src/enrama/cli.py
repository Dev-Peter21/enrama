"""Human-facing Typer commands over reusable configuration/build/preview APIs."""

from collections.abc import Callable
from importlib.metadata import version
from pathlib import Path
from typing import Annotated

import typer

from .config import ConfigurationError
from .core import (
    AssetEnvironmentError,
    AssetError,
    BuildError,
    RenderError,
    build_site,
    validate_project,
)
from .preview import run_preview
from .project import init_project

app = typer.Typer(
    add_completion=False,
    invoke_without_command=True,
    pretty_exceptions_enable=False,
    help="Your links. Your hosting. Your rules.",
)


def _run(action: Callable[[], object]) -> None:
    try:
        action()
    except typer.Exit:
        raise
    except KeyboardInterrupt:
        typer.echo("Interrupted before completion.", err=True)
        raise typer.Exit(130) from None
    except (
        ConfigurationError,
        AssetError,
        BuildError,
        RenderError,
        AssetEnvironmentError,
    ) as error:
        if isinstance(error, ConfigurationError):
            code = 3 if error.category == "read_error" else 1
        elif isinstance(error, AssetError):
            code = 1 if error.kind == "invalid_input" else 3
        elif isinstance(error, AssetEnvironmentError):
            code = 70
        else:
            code = {"invalid_input": 1, "operational": 3, "internal": 70}[error.kind]
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(code) from None
    except Exception:
        typer.echo(
            "Internal error. Preserve the project and report the installed Enrama version.",
            err=True,
        )
        raise typer.Exit(70) from None


@app.callback()
def root(
    ctx: typer.Context,
    show_version: Annotated[
        bool,
        typer.Option("--version", is_eager=True, help="Show the installed version."),
    ] = False,
) -> None:
    if show_version:
        typer.echo("Enrama " + version("enrama"))
        raise typer.Exit()
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


@app.command()
def init(
    destination: Annotated[
        Path,
        typer.Argument(help="New client directory; its parent must already exist."),
    ],
) -> None:
    def create() -> None:
        init_project(destination)
        typer.echo(
            "Created client project. Edit enrama.yaml, then run enrama validate."
        )

    _run(create)


@app.command()
def validate(
    config: Annotated[
        Path,
        typer.Option(
            "--config",
            help="Selected YAML; defaults to enrama.yaml in the current directory.",
        ),
    ] = Path("enrama.yaml"),
) -> None:
    def check() -> None:
        validate_project(config)
        typer.echo("Configuration and local assets are valid.")

    _run(check)


@app.command()
def build(
    config: Annotated[Path, typer.Option("--config")] = Path("enrama.yaml"),
) -> None:
    def generate() -> None:
        result = build_site(config)
        for warning in result.warnings:
            typer.echo("Warning: " + warning, err=True)
        typer.echo(f"Built {len(result.files)} files in dist/.")

    _run(generate)


@app.command()
def preview(
    config: Annotated[Path, typer.Option("--config")] = Path("enrama.yaml"),
    port: Annotated[int, typer.Option("--port", min=1, max=65535)] = 8000,
) -> None:
    _run(
        lambda: run_preview(
            config,
            port,
            lambda url: typer.echo(
                "Preview: " + url + " (Ctrl+C to stop; restart to rebuild)"
            ),
        )
    )
