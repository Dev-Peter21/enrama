"""Generate or check the repository's model-derived editor schema."""

import argparse
import sys
from pathlib import Path

from enrama.config.schema import generate_schema


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true", help="Check without writing files"
    )
    args = parser.parse_args()
    output = Path(__file__).resolve().parents[1] / "schemas/enrama-v1.schema.json"
    try:
        if output.parent.is_symlink() or output.is_symlink():
            raise OSError("Schema directory and artifact must not be symbolic links")
        expected = generate_schema()
        if args.check:
            if not output.exists() or output.read_bytes() != expected:
                print(
                    "Schema artifact is missing or stale. Run: uv run --locked python scripts/schema.py",
                    file=sys.stderr,
                )
                return 1
            print("Schema artifact is current.")
        else:
            output.parent.mkdir(exist_ok=True)
            output.write_bytes(expected)
            print("Generated schemas/enrama-v1.schema.json.")
    except OSError:
        print(
            "Schema artifact could not be read or written. Check regular paths, symlinks and permissions.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
