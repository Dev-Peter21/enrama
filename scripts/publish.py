"""Guard manual production publication. Run only from the reviewed main workflow."""

import argparse
import hashlib
import io
import json
import os
import re
import stat
import subprocess
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.parse import urlsplit

import _publish_remote as remote
import release

VERSION = "0.1.0"
TAG = "v" + VERSION
ARCHIVES = {f"enrama-{VERSION}-py3-none-any.whl", f"enrama-{VERSION}.tar.gz"}
FILES = ARCHIVES | {release.SCHEMA, "release.json", "SHA256SUMS"}
MATRIX = [("linux", p) for p in ("3.12", "3.13", "3.14", "3.15")] + [
    ("macos", "3.12"),
    ("windows", "3.12"),
]


@dataclass(frozen=True)
class Context:
    sha: str
    run: int
    artifact: int
    digest: str


def context() -> Context:
    sha = os.environ.get("SOURCE_SHA", "")
    digest = os.environ.get("CANDIDATE_ZIP_SHA256", "")
    run = os.environ.get("PREPARATION_RUN_ID", "")
    artifact = os.environ.get("CANDIDATE_ARTIFACT_ID", "")
    release.identity(sha, VERSION)
    if (
        not re.fullmatch(r"[0-9a-f]{64}", digest)
        or not re.fullmatch(r"[1-9][0-9]{0,19}", run)
        or not re.fullmatch(r"[1-9][0-9]{0,19}", artifact)
        or os.environ.get("PUBLICATION_AUTHORIZATION")
        != f"publish enrama=={VERSION} {sha} {run} {artifact} {digest}"
    ):
        raise ValueError("Exact candidate-bound production authorization is required")
    expected = {
        "GITHUB_EVENT_NAME": "workflow_dispatch",
        "GITHUB_REPOSITORY": release.REPOSITORY,
        "GITHUB_REF": "refs/heads/main",
        "GITHUB_SHA": sha,
        "GITHUB_WORKFLOW_REF": f"{release.REPOSITORY}/.github/workflows/publish.yml@refs/heads/main",
    }
    if any(os.environ.get(k) != v for k, v in expected.items()):
        raise ValueError(
            "Publication requires the exact reviewed main workflow dispatch"
        )
    return Context(sha, int(run), int(artifact), digest)


def successful_jobs(data: Any, names: set[str]) -> None:
    jobs = data.get("jobs", [])
    if (
        data.get("total_count") != len(names)
        or len(jobs) != len(names)
        or {j["name"] for j in jobs} != names
        or any(
            j.get("status") != "completed" or j.get("conclusion") != "success"
            for j in jobs
        )
    ):
        raise ValueError("Required verification jobs have not all succeeded")


def validate_preparation(
    c: Context, run: Any, jobs: Any, artifact: Any, main: str
) -> None:
    expected = {
        "id": c.run,
        "head_sha": c.sha,
        "head_branch": "main",
        "event": "workflow_dispatch",
        "path": ".github/workflows/release.yml",
        "status": "completed",
        "conclusion": "success",
    }
    if (
        main != c.sha
        or any(run.get(k) != v for k, v in expected.items())
        or type(run.get("run_attempt")) is not int
        or run["run_attempt"] <= 0
        or run.get("head_repository", {}).get("full_name") != release.REPOSITORY
    ):
        raise ValueError("Preparation is not a successful exact-source main run")
    successful_jobs(
        jobs,
        {"Prepare canonical candidate"}
        | {f"Candidate ({o}, Python {p})" for o, p in MATRIX},
    )
    if (
        artifact.get("id") != c.artifact
        or artifact.get("name") != "r03-candidate-" + c.sha
        or artifact.get("expired") is not False
        or artifact.get("digest") != "sha256:" + c.digest
        or artifact.get("workflow_run", {}).get("id") != c.run
        or artifact.get("workflow_run", {}).get("head_sha") != c.sha
        or artifact.get("workflow_run", {}).get("head_branch") != "main"
    ):
        raise ValueError("Candidate artifact identity, digest or retention differs")


def extract_candidate(data: bytes, digest: str, output: Path) -> None:
    if hashlib.sha256(data).hexdigest() != digest:
        raise ValueError("Original artifact ZIP digest differs")
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        members = archive.infolist()
        if (
            len(members) != len(FILES)
            or {m.filename for m in members} != FILES
            or sum(m.file_size for m in members) > remote.LIMIT
            or any(m.is_dir() or stat.S_ISLNK(m.external_attr >> 16) for m in members)
        ):
            raise ValueError("Unsafe or unexpected candidate ZIP inventory")
        output.mkdir()
        for member in members:
            with (output / member.filename).open("xb") as stream:
                stream.write(archive.read(member))


def candidate(c: Context, output: Path) -> None:
    release.check_source(Path.cwd(), c.sha, VERSION, True)
    run = remote.gh(f"actions/runs/{c.run}")
    attempt = run["run_attempt"]
    jobs = remote.gh(f"actions/runs/{c.run}/attempts/{attempt}/jobs?per_page=100")
    artifact = remote.gh(f"actions/artifacts/{c.artifact}")
    main = remote.gh("git/ref/heads/main")["object"]["sha"]
    validate_preparation(c, run, jobs, artifact, main)
    extract_candidate(
        remote.gh_bytes(f"actions/artifacts/{c.artifact}/zip"), c.digest, output
    )
    release.verify(output, c.sha, VERSION)
    record = json.loads(release.regular(output / "release.json"))
    if (
        record["run_id"] != str(c.run)
        or record["run_attempt"] != str(attempt)
        or record["source_ref"] != "refs/heads/main"
        or record["source_ci"] is None
    ):
        raise ValueError("Bundle is not the original verified main preparation")
    ci = record["source_ci"]
    observed = remote.gh(f"actions/runs/{ci['databaseId']}")
    if any(
        observed.get(k) != v
        for k, v in {
            "head_sha": c.sha,
            "head_branch": "main",
            "event": "push",
            "path": ".github/workflows/ci.yml",
            "status": "completed",
            "conclusion": "success",
        }.items()
    ):
        raise ValueError("Original exact-source main CI is no longer successful")
    ensure_tag(c.sha, create=False)
    ensure_release(output, release_notes(c), write=False)
    print(
        release.canonical(
            {
                "source_sha": c.sha,
                "preparation_run": c.run,
                "artifact": c.artifact,
                "artifact_zip_sha256": c.digest,
                "files": record["files"],
            }
        ).decode()
    )


def public_state(bundle: Path) -> list[str]:
    data = remote.public_json(f"https://pypi.org/pypi/enrama/{VERSION}/json")
    if data is None:
        if remote.public_json("https://pypi.org/pypi/enrama/json") is not None:
            raise ValueError(
                "The project name exists without the intended first version"
            )
        return sorted(ARCHIVES)
    info = data["info"]
    if any(
        info.get(k) != v
        for k, v in {
            "name": "enrama",
            "version": VERSION,
            "requires_python": ">=3.12",
        }.items()
    ):
        raise ValueError("Public package identity differs")
    seen: set[str] = set()
    for file in data["urls"]:
        name = file["filename"]
        if name not in ARCHIVES or name in seen:
            raise ValueError("Unexpected or duplicate public archive")
        original = release.regular(bundle / name)
        url = urlsplit(file["url"])
        if (
            file["digests"]["sha256"] != hashlib.sha256(original).hexdigest()
            or file["size"] != len(original)
            or file.get("yanked") is not False
            or url.scheme != "https"
            or url.netloc != "files.pythonhosted.org"
        ):
            raise ValueError(
                "Public archive conflicts with original bytes or is yanked"
            )
        if remote.public_bytes(file["url"]) != original:
            raise ValueError(
                "Actual public download differs from the original candidate"
            )
        seen.add(name)
    return sorted(ARCHIVES - seen)


def stage(bundle: Path, output: Path) -> bool:
    missing = public_state(bundle)
    output.mkdir()
    for name in missing:
        with (output / name).open("xb") as stream:
            stream.write(release.regular(bundle / name))
    print(
        json.dumps(
            {"missing": missing, "destination": "https://upload.pypi.org/legacy/"}
        )
    )
    return bool(missing)


def ensure_tag(sha: str, *, create: bool = True) -> None:
    tag = remote.gh(f"git/ref/tags/{TAG}", missing=True)
    if tag is None:
        if create:
            remote.gh(
                "git/refs", method="POST", data={"ref": "refs/tags/" + TAG, "sha": sha}
            )
        return
    target = tag["object"]
    for _ in range(5):
        if target["type"] != "tag":
            break
        target = remote.gh("git/tags/" + target["sha"])["object"]
    if target.get("type") != "commit" or target.get("sha") != sha:
        raise ValueError("Existing tag points elsewhere; tags are never moved")


def missing_assets(state: Any, notes: str, expected: dict[str, bytes]) -> list[str]:
    if (
        state["tag_name"] != TAG
        or state["body"] != notes
        or state["prerelease"] is not False
    ):
        raise ValueError("Existing release identity or reviewed notes differ")
    seen: set[str] = set()
    for asset in state["assets"]:
        name = asset["name"]
        if name not in expected or name in seen or asset["size"] != len(expected[name]):
            raise ValueError("Existing GitHub release asset conflicts")
        if remote.gh_bytes(f"releases/assets/{asset['id']}") != expected[name]:
            raise ValueError("Existing GitHub release asset bytes differ")
        seen.add(name)
    return sorted(expected.keys() - seen)


def find_release() -> Any:
    state = remote.gh(f"releases/tags/{TAG}", missing=True)
    if state is not None:
        return state
    # The by-tag endpoint returns published releases, not drafts. A write-token
    # retry must find its existing draft rather than creating another one.
    releases = remote.gh("releases?per_page=100")
    if not isinstance(releases, list) or len(releases) >= 100:
        raise ValueError("Release listing is ambiguous; inspect manually")
    matches = [r for r in releases if r["tag_name"] == TAG]
    if len(matches) > 1:
        raise ValueError("Multiple matching release drafts; inspect manually")
    return matches[0] if matches else None


def ensure_release(bundle: Path, notes: str, *, write: bool = True) -> None:
    state = find_release()
    if state is None:
        if not write:
            return
        state = remote.gh(
            "releases",
            method="POST",
            data={
                "tag_name": TAG,
                "name": "Enrama " + VERSION,
                "body": notes,
                "draft": True,
                "prerelease": False,
            },
        )
    expected = {p.name: release.regular(p) for p in bundle.iterdir()}
    missing = missing_assets(state, notes, expected)
    if not write:
        return
    if missing:
        remote.command(
            "release",
            "upload",
            TAG,
            *(str(bundle / n) for n in missing),
            "--repo",
            release.REPOSITORY,
        )
        state = find_release()
        if missing_assets(state, notes, expected):
            raise ValueError(
                "Cannot confirm uploaded assets; preserve draft and retry originals"
            )
    if state["draft"]:
        updated = remote.gh(
            f"releases/{state['id']}", method="PATCH", data={"draft": False}
        )
        if updated.get("draft") is not False or missing_assets(
            updated, notes, expected
        ):
            raise ValueError(
                "Cannot confirm completed release; inspect before retrying"
            )


def release_notes(c: Context) -> str:
    notes = release.regular(Path("docs/release-notes/0.1.0.md")).decode("utf-8")
    return (
        notes
        + f"\nSource: `{c.sha}`\nPreparation: https://github.com/{release.REPOSITORY}/actions/runs/{c.run}\nArtifact ZIP SHA-256: `{c.digest}`\n"
    )


def finalize(c: Context, bundle: Path) -> None:
    if os.environ.get("GITHUB_JOB") != "finalize":
        raise ValueError("Finalization is only available in the approved finalize job")
    current = os.environ["GITHUB_RUN_ID"]
    attempt = os.environ["GITHUB_RUN_ATTEMPT"]
    if not current.isdecimal() or not attempt.isdecimal():
        raise ValueError("Invalid current workflow identity")
    jobs = remote.gh(f"actions/runs/{current}/attempts/{attempt}/jobs?per_page=100")
    names = {f"Public ({o}, Python {p})" for o, p in MATRIX}
    selected = [j for j in jobs["jobs"] if j["name"] in names]
    successful_jobs({"jobs": selected, "total_count": len(selected)}, names)
    if public_state(bundle):
        raise ValueError("Public files are incomplete; finalization is forbidden")
    notes = release_notes(c)
    ensure_tag(c.sha)
    ensure_release(bundle, notes)
    print(
        "Matching GitHub release finalized; R03 still requires maintainer acceptance."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command", choices=("candidate", "stage", "public-files", "finalize")
    )
    args = parser.parse_args()
    try:
        c = context()
        bundle = Path("reports/candidate")
        if args.command == "candidate":
            candidate(c, bundle)
        else:
            release.verify(bundle, c.sha, VERSION)
            if args.command == "stage":
                needed = stage(bundle, Path("reports/upload"))
                with Path(os.environ["GITHUB_OUTPUT"]).open(
                    "a", encoding="utf-8"
                ) as stream:
                    stream.write(f"upload_needed={str(needed).lower()}\n")
            elif args.command == "public-files":
                if public_state(bundle):
                    raise ValueError("Production files are incomplete")
                print("Actual public wheel/sdist bytes match the original candidate.")
            else:
                finalize(c, bundle)
    except (
        ValueError,
        OSError,
        KeyError,
        TypeError,
        URLError,
        subprocess.SubprocessError,
        zipfile.BadZipFile,
    ) as error:
        # Avoid echoing subprocess output: a publisher must never log credentials.
        parser.exit(
            1,
            f"Publication stopped: {str(error) if isinstance(error, ValueError) else type(error).__name__}; preserve originals and inspect retained evidence.\n",
        )


if __name__ == "__main__":
    main()
