"""Create a small client starter without overwriting any existing destination."""

import os
from pathlib import Path

from .core._build_errors import BuildError
from .core._manifest import remove_owned

STARTER = """schema_version: 1
site:
  title: "My links"
  description: "Find my work and get in touch."
  language: "en"
profile:
  name: "Your name"
  bio: "A little about you."
theme:
  name: "minimal"
links:
  - id: website
    title: "Visit my website"
    url: "https://example.com"
    icon: "globe"
socials: []
"""


def init_project(destination: str | Path) -> Path:
    target = Path(os.path.abspath(destination))
    created = False
    expected = {"enrama.yaml", ".gitignore"}
    try:
        parent = target.parent.resolve(strict=True)
        target = parent / target.name
        target.mkdir()
        created = True
        (target / "assets").mkdir()
        with (target / "enrama.yaml").open("xb") as f:
            f.write(STARTER.encode("utf-8"))
        with (target / ".gitignore").open("xb") as f:
            f.write(b"dist/\n.enrama/\n")
        return target
    except BaseException as error:
        if created:
            try:
                # Empty starter assets is known; unknown injected content is kept.
                if (target / "assets").is_symlink():
                    raise OSError("Changed starter")
                (target / "assets").rmdir()
                remove_owned(target, expected)
            except (OSError, BuildError):
                raise BuildError(
                    "operational",
                    "init_cleanup",
                    "Starter creation failed and partial data remains",
                    "Preserve the destination and inspect its contents manually",
                ) from None
        if isinstance(error, OSError):
            raise BuildError(
                "operational",
                "init_conflict",
                "The destination already exists or its parent is unavailable",
                "Choose an absent destination inside an existing writable directory",
            ) from None
        raise
