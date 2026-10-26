"""User-visible command behavior and F01 error codes."""

from pathlib import Path

import pytest


@pytest.mark.parametrize(
    "args", [[], ["--help"], ["--version"], ["build", "--help"], ["preview", "--help"]]
)
def test_help_version_without_project(
    args: list[str], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from typer.testing import CliRunner

    from enrama.cli import app

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 0 and result.stdout
    assert list(tmp_path.iterdir()) == []


def test_init_validate_build_workflow(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from typer.testing import CliRunner

    from enrama.cli import app

    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    result = runner.invoke(app, ["init", "client"])
    assert result.exit_code == 0, result.output
    root = tmp_path / "client"
    assert (root / "enrama.yaml").is_file() and (root / "assets").is_dir()
    assert (
        "dist/" in (root / ".gitignore").read_text()
        and ".enrama/" in (root / ".gitignore").read_text()
    )
    assert not (root / "dist").exists()
    result = runner.invoke(app, ["validate", "--config", "client/enrama.yaml"])
    assert result.exit_code == 0, result.output
    assert not (root / ".enrama").exists()
    result = runner.invoke(app, ["build", "--config", "client/enrama.yaml"])
    assert result.exit_code == 0, result.output
    assert (root / "dist/index.html").is_file()
    before = (root / "enrama.yaml").read_bytes()
    result = runner.invoke(app, ["init", "client"])
    assert result.exit_code == 3
    assert (root / "enrama.yaml").read_bytes() == before


@pytest.mark.parametrize(
    "args,expected",
    [
        (["validate"], 1),
        (["build"], 1),
        (["init"], 2),
        (["unknown"], 2),
        (["build", "--force"], 2),
        (["build", "--output", "other"], 2),
        (["preview", "--port", "0"], 2),
        (["preview", "--port", "65536"], 2),
        (["preview", "--port", "abc"], 2),
        (["preview", "--host", "localhost"], 2),
        (["init", "missing-parent/client"], 3),
    ],
)
def test_errors_have_expected_codes(
    args: list[str], expected: int, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from typer.testing import CliRunner

    from enrama.cli import app

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, args)
    assert result.exit_code == expected, result.output
    assert "Traceback" not in result.output
    assert not (tmp_path / "dist").exists()


def test_existing_output_and_incomplete_transaction_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from typer.testing import CliRunner

    from enrama.cli import app

    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    runner.invoke(app, ["init", "client"])
    config = ["--config", "client/enrama.yaml"]
    assert runner.invoke(app, ["build", *config]).exit_code == 0
    (tmp_path / "client/dist/extra.txt").write_text("PRESERVE")
    result = runner.invoke(app, ["build", *config])
    assert result.exit_code == 3
    assert (tmp_path / "client/dist/extra.txt").read_text() == "PRESERVE"
    (tmp_path / "client/dist/extra.txt").unlink()
    (tmp_path / "client/.enrama/transaction.json").write_text("{}")
    result = runner.invoke(app, ["build", *config])
    assert result.exit_code == 3
    assert "incomplete" in result.output.lower()


def test_internal_defect_and_interrupt_map_without_tracebacks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from typer.testing import CliRunner

    from enrama import cli

    monkeypatch.chdir(tmp_path)

    def broken(source: Path) -> object:
        raise RuntimeError("PRIVATE PAYLOAD")

    monkeypatch.setattr(cli, "build_site", broken)
    result = CliRunner().invoke(cli.app, ["build"])
    assert result.exit_code == 70
    assert "PRIVATE" not in result.output and "Traceback" not in result.output

    def interrupt(source: Path) -> object:
        raise KeyboardInterrupt

    monkeypatch.setattr(cli, "build_site", interrupt)
    assert CliRunner().invoke(cli.app, ["build"]).exit_code == 130


def test_init_preserves_file_created_by_another_actor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from enrama.core import BuildError
    from enrama.project import init_project

    real = Path.open

    def collide(path: Path, *args: object, **kwargs: object) -> object:
        if path.name == "enrama.yaml" and args and args[0] == "xb":
            with real(path, "wb") as stream:
                stream.write(b"FOREIGN DATA")
        return real(path, *args, **kwargs)  # type: ignore[call-overload]

    monkeypatch.setattr(Path, "open", collide)
    with pytest.raises(BuildError):
        init_project(tmp_path / "client")
    assert (tmp_path / "client/enrama.yaml").read_bytes() == b"FOREIGN DATA"
