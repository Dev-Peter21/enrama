"""Read only the selected regular file, with bounded bytes and normal interruption."""

import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from enrama.config import ConfigurationError, EnramaConfig

MINIMAL = b"""schema_version: 1
site: {title: Shop, description: Shop, language: en}
profile: {name: Shop, avatar: ./assets/missing.png}
"""


def load(path: str | Path = "enrama.yaml") -> EnramaConfig:
    from enrama.config import load_config

    return load_config(path)


def test_exact_current_directory_discovery_without_parent_search(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "enrama.yaml").write_bytes(MINIMAL)
    child = tmp_path / "child"
    child.mkdir()
    monkeypatch.chdir(child)
    with pytest.raises(ConfigurationError) as caught:
        load()
    assert caught.value.category == "missing_file"
    assert Path.cwd() == child
    assert load("../enrama.yaml").profile.avatar == "./assets/missing.png"
    assert load(tmp_path / "enrama.yaml").profile.name == "Shop"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["child", "enrama.yaml"]
    assert list(child.iterdir()) == []


def test_selected_file_only_and_unchanged_input(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "selected.yaml"
    path.write_bytes(MINIMAL)
    opens: list[Path] = []
    real_open = os.open

    def observed(
        file: str | bytes | os.PathLike[str] | os.PathLike[bytes],
        flags: int,
        mode: int = 0o777,
        *,
        dir_fd: int | None = None,
    ) -> int:
        opens.append(Path(os.fsdecode(file)))
        assert flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC) == 0
        return real_open(file, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(os, "open", observed)
    assert load(path).profile.avatar == "./assets/missing.png"
    assert opens == [path]
    assert path.read_bytes() == MINIMAL
    assert sorted(p.name for p in tmp_path.iterdir()) == ["selected.yaml"]


@pytest.mark.parametrize("kind", ["directory", "permission", "other"])
def test_operational_failures_are_safe_read_errors(
    kind: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "input"
    if kind == "directory":
        path.mkdir()
    else:

        def fail(*args: object, **kwargs: object) -> int:
            if kind == "permission":
                raise PermissionError("SECRET operating system payload")
            raise OSError("SECRET operating system payload")

        monkeypatch.setattr(os, "open", fail)
    with pytest.raises(ConfigurationError) as caught:
        load(path)
    assert caught.value.category == "read_error"
    assert "SECRET" not in str(caught.value)
    assert caught.value.diagnostics[0].position is None


@pytest.mark.skipif(
    not hasattr(os, "mkfifo"), reason="FIFOs are unavailable on Windows"
)
def test_fifo_is_rejected_without_waiting_for_a_writer(tmp_path: Path) -> None:
    path = tmp_path / "pipe"
    os.mkfifo(path)
    with pytest.raises(ConfigurationError) as caught:
        load(path)
    assert caught.value.category == "read_error"


def test_actual_read_has_limit_plus_one_even_when_metadata_is_stale(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from enrama.config._yaml import MAX_BYTES

    path = tmp_path / "input.yaml"
    base = MINIMAL + b"#"
    path.write_bytes(base + b"x" * (MAX_BYTES + 20 - len(base)))
    real_read, real_stat = os.read, os.fstat
    requests: list[int] = []
    received: list[int] = []

    def stale(fd: int) -> SimpleNamespace:
        return SimpleNamespace(st_size=0, st_mode=real_stat(fd).st_mode)

    def observed(fd: int, size: int) -> bytes:
        requests.append(size)
        # Exercise partial reads as well as the total bound.
        data = real_read(fd, min(size, 12345))
        received.append(len(data))
        return data

    monkeypatch.setattr(os, "fstat", stale)
    monkeypatch.setattr(os, "read", observed)
    with pytest.raises(ConfigurationError) as caught:
        load(path)
    assert caught.value.category == "resource_limit"
    assert sum(received) == MAX_BYTES + 1
    assert max(requests) <= MAX_BYTES + 1


def test_file_byte_limit_with_bom_comments_and_no_asset_access(tmp_path: Path) -> None:
    path = tmp_path / "enrama.yaml"
    base = b"\xef\xbb\xbf" + MINIMAL + b"#"
    path.write_bytes(base + b"x" * (1_048_576 - len(base)))
    assert load(path).profile.name == "Shop"
    with path.open("ab") as stream:
        stream.write(b"x")
    with pytest.raises(ConfigurationError) as caught:
        load(path)
    assert caught.value.category == "resource_limit"


@pytest.mark.parametrize("exception", [KeyboardInterrupt, RuntimeError, OSError])
@pytest.mark.parametrize("stage", ["open", "fstat", "read"])
def test_failure_cleanup_and_unexpected_defect_propagation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    exception: type[BaseException],
    stage: str,
) -> None:
    path = tmp_path / "input.yaml"
    path.write_bytes(MINIMAL)
    closed: list[int] = []
    real_close = os.close

    def fail(*args: object, **kwargs: object) -> int:
        raise exception("SECRET")

    def observed_close(fd: int) -> None:
        closed.append(fd)
        real_close(fd)

    monkeypatch.setattr(os, stage, fail)
    monkeypatch.setattr(os, "close", observed_close)
    expected = ConfigurationError if exception is OSError else exception
    with pytest.raises(expected) as caught:
        load(path)
    if exception is OSError:
        assert isinstance(caught.value, ConfigurationError)
        assert caught.value.category == "read_error"
        assert "SECRET" not in str(caught.value)
    assert len(closed) == (0 if stage == "open" else 1)
