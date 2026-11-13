"""Prepare or verify immutable release files; never configure or publish anything."""

import argparse
import hashlib
import io
import json
import os
import re
import stat
import subprocess
import tarfile
import tomllib
import zipfile
from email import policy
from email.parser import BytesParser
from pathlib import Path, PurePosixPath
from typing import Any

SCHEMA = "enrama-v1.schema.json"
REPOSITORY = "Dev-Peter21/enrama"


def canonical(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def regular(path: Path, limit: int = 64 * 1024 * 1024) -> bytes:
    info = path.lstat()
    if (
        not stat.S_ISREG(info.st_mode)
        or getattr(info, "st_file_attributes", 0) & 0x400
        or info.st_size > limit
    ):
        raise ValueError("Expected a bounded regular file, without links")
    return path.read_bytes()


def directory(path: Path) -> None:
    info = path.lstat()
    if not stat.S_ISDIR(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
        raise ValueError("Expected a real directory, without links")


def identity(sha: str, version: str) -> None:
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise ValueError("Expected a full lowercase source SHA")
    if not re.fullmatch(r"0\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)", version):
        raise ValueError("Expected an explicit 0.x.y release version")


def git(source: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(source), *args],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def check_source(source: Path, sha: str, version: str, require_main: bool) -> None:
    identity(sha, version)
    directory(source)
    if Path(git(source, "rev-parse", "--show-toplevel")).resolve() != source.resolve():
        raise ValueError("Source must be the Git repository root")
    if git(source, "rev-parse", "HEAD") != sha or git(source, "status", "--porcelain"):
        raise ValueError("Source SHA differs or the source checkout is dirty")
    project = tomllib.loads(regular(source / "pyproject.toml").decode("utf-8"))[
        "project"
    ]
    if project["name"] != "enrama" or project["version"] != version:
        raise ValueError("Project name/version differs from the requested candidate")
    if require_main and (
        os.environ.get("GITHUB_REF") != "refs/heads/main"
        or os.environ.get("GITHUB_REPOSITORY") != REPOSITORY
        or os.environ.get("GITHUB_SHA") != sha
    ):
        raise ValueError(
            "Manual preparation requires this repository's exact main dispatch"
        )


def source_ci(data: Any, sha: str) -> dict[str, Any]:
    if not isinstance(data, list) or len(data) != 1 or not isinstance(data[0], dict):
        raise ValueError("Expected one exact-source CI run")
    run = data[0]
    expected = {
        "headSha": sha,
        "headBranch": "main",
        "event": "push",
        "workflowName": "CI",
        "status": "completed",
        "conclusion": "success",
    }
    if (
        any(run.get(key) != value for key, value in expected.items())
        or type(run.get("databaseId")) is not int
        or run["databaseId"] <= 0
    ):
        raise ValueError("Main push CI has not succeeded for this exact source")
    return {"databaseId": run["databaseId"], **expected}


def metadata(data: bytes, version: str) -> None:
    record = BytesParser(policy=policy.default).parsebytes(data)
    for key, value in {
        "Name": "enrama",
        "Version": version,
        "Requires-Python": ">=3.12",
        "License-Expression": "MIT",
    }.items():
        if record.get_all(key) != [value]:
            raise ValueError("Archive metadata differs from the release contract")


def validated_payloads(data: dict[str, bytes], version: str) -> dict[str, bytes]:
    names = [f"enrama-{version}-py3-none-any.whl", f"enrama-{version}.tar.gz", SCHEMA]
    schema = json.loads(data[SCHEMA])
    if (
        not isinstance(schema, dict)
        or schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema"
    ):
        raise ValueError("Invalid checked configuration schema")
    with zipfile.ZipFile(io.BytesIO(data[names[0]])) as wheel:
        member = f"enrama-{version}.dist-info/METADATA"
        if (
            wheel.namelist().count(member) != 1
            or wheel.getinfo(member).file_size > 1024 * 1024
        ):
            raise ValueError("Expected one bounded wheel metadata record")
        metadata(wheel.read(member), version)
    with tarfile.open(fileobj=io.BytesIO(data[names[1]]), mode="r:gz") as sdist:
        prefix = f"enrama-{version}/"
        members = sdist.getmembers()
        for item in members:
            path = PurePosixPath(item.name)
            if (
                path.is_absolute()
                or ".." in path.parts
                or "\\" in item.name
                or not (item.isfile() or item.isdir())
            ):
                raise ValueError("Unsafe source archive member")
        for name in ("PKG-INFO", "pyproject.toml", "schemas/" + SCHEMA):
            selected = [item for item in members if item.name == prefix + name]
            if (
                len(selected) != 1
                or not selected[0].isfile()
                or selected[0].size > 1024 * 1024
            ):
                raise ValueError("Expected one bounded source metadata/schema record")
            stream = sdist.extractfile(selected[0])
            if stream is None:
                raise ValueError("Missing source archive record")
            content = stream.read()
            if name == "PKG-INFO":
                metadata(content, version)
            elif name == "pyproject.toml":
                project = tomllib.loads(content.decode("utf-8"))["project"]
                if project.get("name") != "enrama" or project.get("version") != version:
                    raise ValueError("Source project metadata differs")
            elif content != data[SCHEMA]:
                raise ValueError("Source archive and checked schema differ")
    return data


def payloads(folder: Path, version: str) -> dict[str, bytes]:
    names = [f"enrama-{version}-py3-none-any.whl", f"enrama-{version}.tar.gz", SCHEMA]
    return validated_payloads({name: regular(folder / name) for name in names}, version)


def inventory(data: dict[str, bytes]) -> list[dict[str, object]]:
    return [
        {
            "name": name,
            "size": len(content),
            "sha256": hashlib.sha256(content).hexdigest(),
        }
        for name, content in sorted(data.items())
    ]


def checksums(data: dict[str, bytes]) -> bytes:
    return "".join(
        f"{hashlib.sha256(content).hexdigest()}  {name}\n"
        for name, content in sorted(data.items())
    ).encode("ascii")


def bundle(
    source: Path,
    archives: Path,
    output: Path,
    sha: str,
    version: str,
    require_main: bool,
    ci_report: Path | None,
) -> None:
    check_source(source, sha, version, require_main)
    directory(archives)
    archive_names = {f"enrama-{version}-py3-none-any.whl", f"enrama-{version}.tar.gz"}
    if {p.name for p in archives.iterdir()} != archive_names:
        raise ValueError("Expected exactly one matching wheel and source distribution")
    ci = source_ci(json.loads(regular(ci_report)), sha) if ci_report else None
    if require_main and ci is None:
        raise ValueError("Exact-source successful main CI evidence is required")
    data = {name: regular(archives / name) for name in archive_names}
    data[SCHEMA] = regular(source / "schemas" / SCHEMA, 1024 * 1024)
    validated_payloads(data, version)
    # Validate before creating output. Never overwrite or clean uncertain data.
    output.mkdir()
    for name, content in data.items():
        with (output / name).open("xb") as f:
            f.write(content)
    data = payloads(output, version)
    record = {
        "format_version": 1,
        "package": "enrama",
        "version": version,
        "tag": "v" + version,
        "source_sha": sha,
        "source_ref": os.environ.get("GITHUB_REF"),
        "source_ci": ci,
        "repository": REPOSITORY,
        "run_id": os.environ.get("GITHUB_RUN_ID"),
        "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
        "publication_authorized": False,
        "files": inventory(data),
    }
    data["release.json"] = canonical(record)
    with (output / "release.json").open("xb") as f:
        f.write(data["release.json"])
    with (output / "SHA256SUMS").open("xb") as f:
        f.write(checksums(data))


def verify(folder: Path, sha: str, version: str) -> None:
    identity(sha, version)
    directory(folder)
    names = {
        f"enrama-{version}-py3-none-any.whl",
        f"enrama-{version}.tar.gz",
        SCHEMA,
        "release.json",
        "SHA256SUMS",
    }
    if {p.name for p in folder.iterdir()} != names:
        raise ValueError("Bundle inventory differs")
    data = payloads(folder, version)
    document = regular(folder / "release.json", 1024 * 1024)
    record = json.loads(document)
    keys = {
        "format_version",
        "package",
        "version",
        "tag",
        "source_sha",
        "source_ref",
        "source_ci",
        "repository",
        "run_id",
        "run_attempt",
        "publication_authorized",
        "files",
    }
    if (
        not isinstance(record, dict)
        or set(record) != keys
        or canonical(record) != document
    ):
        raise ValueError("Invalid canonical release record")
    for key, value in {
        "format_version": 1,
        "package": "enrama",
        "version": version,
        "tag": "v" + version,
        "source_sha": sha,
        "repository": REPOSITORY,
        "publication_authorized": False,
    }.items():
        if type(record[key]) is not type(value) or record[key] != value:
            raise ValueError("Bundle source/version/authorization differs")
    if canonical(record["files"]) != canonical(inventory(data)):
        raise ValueError("Bundle file hashes/sizes differ")
    if record["source_ci"] is not None:
        source_ci([record["source_ci"]], sha)
    data["release.json"] = document
    if regular(folder / "SHA256SUMS", 64 * 1024) != checksums(data):
        raise ValueError("Bundle checksums differ")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("check-source", "bundle", "verify"))
    parser.add_argument("--source", type=Path, default=Path.cwd())
    parser.add_argument("--archives", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--bundle", type=Path)
    parser.add_argument("--expected-sha", required=True)
    parser.add_argument("--expected-version", required=True)
    parser.add_argument("--require-main", action="store_true")
    parser.add_argument("--ci-report", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "check-source":
            check_source(
                args.source, args.expected_sha, args.expected_version, args.require_main
            )
            if args.ci_report is not None:
                source_ci(json.loads(regular(args.ci_report)), args.expected_sha)
        elif (
            args.command == "bundle"
            and args.archives is not None
            and args.output is not None
        ):
            bundle(
                args.source,
                args.archives,
                args.output,
                args.expected_sha,
                args.expected_version,
                args.require_main,
                args.ci_report,
            )
        elif args.command == "verify" and args.bundle is not None:
            verify(args.bundle, args.expected_sha, args.expected_version)
        else:
            raise ValueError("Required paths for this command are missing")
    except (
        ValueError,
        OSError,
        KeyError,
        subprocess.CalledProcessError,
        zipfile.BadZipFile,
        tarfile.TarError,
    ) as error:
        parser.exit(1, f"Release preparation failed: {error}\n")
    print("Release preparation check passed; publication is not authorized.")


if __name__ == "__main__":
    main()
