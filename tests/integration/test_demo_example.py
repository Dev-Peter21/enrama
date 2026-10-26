"""A clean developer copy can validate/build the tracked example in both themes."""

import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("theme", ["minimal", "bold"])
def test_tracked_example_cli_builds_complete_self_contained_output(
    theme: str, tmp_path: Path
) -> None:
    client = tmp_path / "client"
    shutil.copytree(
        ROOT / "examples/demo", client, ignore=shutil.ignore_patterns("dist", ".enrama")
    )
    source = client / "enrama.yaml"
    data = yaml.safe_load(source.read_text(encoding="utf-8"))
    data["theme"]["name"] = theme
    source.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    original = {p.name: p.read_bytes() for p in (client / "assets").iterdir()}
    for command in ("validate", "build"):
        result = subprocess.run(
            [sys.executable, "-m", "enrama", command, "--config", str(source)],
            capture_output=True,
            text=True,
            timeout=15,
        )
        assert result.returncode == 0, result.stdout + result.stderr
    html = (client / "dist/index.html").read_text(encoding="utf-8")
    assert f'class="theme-{theme}"' in html
    paths = [
        name
        for name in re.findall(r'(?:src|href)="([^"]+)"', html)
        if name.startswith("assets/")
    ]
    assert len(paths) >= 3 and any(name.endswith(".css") for name in paths)
    assert all((client / "dist" / name).is_file() for name in paths)
    assert (client / "dist/assets/theme/THIRD_PARTY_NOTICES.txt").is_file()
    assert {p.name: p.read_bytes() for p in (client / "assets").iterdir()} == original
