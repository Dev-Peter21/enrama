"""Offline publication gates: no test exchanges credentials or publishes files."""

import hashlib
import importlib
import io
import json
import zipfile
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
import yaml
from test_release import bundle as make_bundle
from test_release import candidate as source_candidate  # noqa: F401

ROOT = Path(__file__).resolve().parents[2]
SHA = "a" * 40
DIGEST = "b" * 64


@pytest.fixture
def pub(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    return importlib.import_module("publish")


@pytest.fixture
def context_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key, value in {
        "SOURCE_SHA": SHA,
        "PREPARATION_RUN_ID": "123",
        "CANDIDATE_ARTIFACT_ID": "456",
        "CANDIDATE_ZIP_SHA256": DIGEST,
        "PUBLICATION_AUTHORIZATION": f"publish enrama==0.1.0 {SHA} 123 456 {DIGEST}",
        "GITHUB_EVENT_NAME": "workflow_dispatch",
        "GITHUB_REPOSITORY": "Dev-Peter21/enrama",
        "GITHUB_REF": "refs/heads/main",
        "GITHUB_SHA": SHA,
        "GITHUB_WORKFLOW_REF": "Dev-Peter21/enrama/.github/workflows/publish.yml@refs/heads/main",
    }.items():
        monkeypatch.setenv(key, value)


def test_exact_dispatch_identity(pub: ModuleType, context_env: None) -> None:
    context = pub.context()
    assert context.sha == SHA and context.run == 123 and context.artifact == 456


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("SOURCE_SHA", "main"),
        ("PREPARATION_RUN_ID", "0"),
        ("CANDIDATE_ARTIFACT_ID", "456;echo bad"),
        ("CANDIDATE_ZIP_SHA256", "B" * 64),
        ("PUBLICATION_AUTHORIZATION", "yes"),
        ("GITHUB_EVENT_NAME", "push"),
        ("GITHUB_REF", "refs/heads/develop"),
        ("GITHUB_REPOSITORY", "fork/enrama"),
        ("GITHUB_SHA", "c" * 40),
        (
            "GITHUB_WORKFLOW_REF",
            "Dev-Peter21/enrama/.github/workflows/release.yml@refs/heads/main",
        ),
    ],
)
def test_reject_floating_authorization(
    pub: ModuleType,
    context_env: None,
    monkeypatch: pytest.MonkeyPatch,
    key: str,
    value: str,
) -> None:
    monkeypatch.setenv(key, value)
    with pytest.raises(ValueError):
        pub.context()


def test_zip_identity_and_exclusive_output(pub: ModuleType, tmp_path: Path) -> None:
    stream = io.BytesIO()
    names = {
        "enrama-0.1.0-py3-none-any.whl",
        "enrama-0.1.0.tar.gz",
        "enrama-v1.schema.json",
        "release.json",
        "SHA256SUMS",
    }
    with zipfile.ZipFile(stream, "w") as z:
        for name in names:
            z.writestr(name, name)
    data = stream.getvalue()
    output = tmp_path / "candidate"
    pub.extract_candidate(data, hashlib.sha256(data).hexdigest(), output)
    assert {p.name for p in output.iterdir()} == names
    with pytest.raises(FileExistsError):
        pub.extract_candidate(data, hashlib.sha256(data).hexdigest(), output)
    with pytest.raises(ValueError):
        pub.extract_candidate(data, DIGEST, tmp_path / "wrong")
    assert not (tmp_path / "wrong").exists()


@pytest.mark.parametrize("name", ["../escape", "/escape", "sub/file", "release.json"])
def test_reject_unsafe_or_duplicate_zip(
    pub: ModuleType, tmp_path: Path, name: str
) -> None:
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as z:
        z.writestr(name, "bad")
    data = stream.getvalue()
    with pytest.raises(ValueError):
        pub.extract_candidate(data, hashlib.sha256(data).hexdigest(), tmp_path / "out")
    assert not (tmp_path / "out").exists()


@pytest.fixture
def public_candidate(tmp_path: Path) -> tuple[Path, dict[str, Any], dict[str, bytes]]:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    payloads = {
        "enrama-0.1.0-py3-none-any.whl": b"wheel",
        "enrama-0.1.0.tar.gz": b"sdist",
    }
    urls = []
    for name, data in payloads.items():
        (bundle / name).write_bytes(data)
        urls.append(
            {
                "filename": name,
                "size": len(data),
                "digests": {"sha256": hashlib.sha256(data).hexdigest()},
                "yanked": False,
                "url": "https://files.pythonhosted.org/packages/" + name,
            }
        )
    return (
        bundle,
        {
            "info": {"name": "enrama", "version": "0.1.0", "requires_python": ">=3.12"},
            "urls": urls,
        },
        payloads,
    )


def test_public_partial_and_complete(
    pub: ModuleType,
    public_candidate: tuple[Path, dict[str, Any], dict[str, bytes]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle, data, payloads = public_candidate
    monkeypatch.setattr(pub.remote, "public_json", lambda _url: data)
    monkeypatch.setattr(
        pub.remote, "public_bytes", lambda url: payloads[url.rsplit("/", 1)[1]]
    )
    assert pub.public_state(bundle) == []
    data["urls"].pop()
    assert pub.public_state(bundle) == ["enrama-0.1.0.tar.gz"]


@pytest.mark.parametrize(
    "problem",
    ["digest", "size", "yanked", "url", "duplicate", "extra", "download", "version"],
)
def test_conflicting_public_state_stops(
    pub: ModuleType,
    public_candidate: tuple[Path, dict[str, Any], dict[str, bytes]],
    monkeypatch: pytest.MonkeyPatch,
    problem: str,
) -> None:
    bundle, data, payloads = public_candidate
    first = data["urls"][0]
    if problem == "digest":
        first["digests"]["sha256"] = DIGEST
    if problem == "size":
        first["size"] = 999
    if problem == "yanked":
        first["yanked"] = True
    if problem == "url":
        first["url"] = "https://attacker.example/file"
    if problem == "duplicate":
        data["urls"].append(first)
    if problem == "extra":
        first["filename"] = "unreviewed.whl"
    if problem == "download":
        payloads[first["filename"]] = b"changed"
    if problem == "version":
        data["info"]["version"] = "0.1.1"
    monkeypatch.setattr(pub.remote, "public_json", lambda _url: data)
    monkeypatch.setattr(
        pub.remote, "public_bytes", lambda url: payloads[url.rsplit("/", 1)[1]]
    )
    with pytest.raises(ValueError):
        pub.public_state(bundle)


def test_missing_version_stops_if_name_taken(
    pub: ModuleType,
    public_candidate: tuple[Path, dict[str, Any], dict[str, bytes]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle, _, payloads = public_candidate
    monkeypatch.setattr(
        pub.remote,
        "public_json",
        lambda url: None if "/0.1.0/" in url else {"info": {"name": "enrama"}},
    )
    with pytest.raises(ValueError):
        pub.public_state(bundle)
    monkeypatch.setattr(pub.remote, "public_json", lambda _url: None)
    assert pub.public_state(bundle) == sorted(payloads)


def test_stage_copies_only_missing_originals(
    pub: ModuleType,
    public_candidate: tuple[Path, dict[str, Any], dict[str, bytes]],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    bundle, _, _ = public_candidate
    monkeypatch.setattr(pub, "public_state", lambda _bundle: ["enrama-0.1.0.tar.gz"])
    output = tmp_path / "upload"
    assert pub.stage(bundle, output) is True
    assert [p.name for p in output.iterdir()] == ["enrama-0.1.0.tar.gz"]
    assert (output / "enrama-0.1.0.tar.gz").read_bytes() == b"sdist"
    monkeypatch.setattr(pub, "public_state", lambda _bundle: [])
    assert pub.stage(bundle, tmp_path / "complete") is False


def test_existing_tag_conflict_never_moves_tag(
    pub: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[tuple[str, str]] = []

    def gh(path: str, **kwargs: Any) -> Any:
        calls.append((path, kwargs.get("method", "GET")))
        return {"object": {"type": "commit", "sha": "c" * 40}}

    monkeypatch.setattr(pub.remote, "gh", gh)
    with pytest.raises(ValueError):
        pub.ensure_tag(SHA)
    assert all(method == "GET" for _, method in calls)


def test_matching_tag_is_reused(
    pub: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[str] = []

    def gh(path: str, **kwargs: Any) -> Any:
        assert kwargs.get("method", "GET") == "GET"
        calls.append(path)
        return {"object": {"type": "commit", "sha": SHA}}

    monkeypatch.setattr(pub.remote, "gh", gh)
    pub.ensure_tag(SHA)
    assert len(calls) == 1


@pytest.fixture
def preparation() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    run = {
        "id": 123,
        "run_attempt": 1,
        "head_sha": SHA,
        "head_branch": "main",
        "event": "workflow_dispatch",
        "path": ".github/workflows/release.yml",
        "status": "completed",
        "conclusion": "success",
        "head_repository": {"full_name": "Dev-Peter21/enrama"},
    }
    names = ["Prepare canonical candidate"] + [
        f"Candidate ({os}, Python {py})"
        for os, py in [
            ("linux", "3.12"),
            ("linux", "3.13"),
            ("linux", "3.14"),
            ("linux", "3.15"),
            ("macos", "3.12"),
            ("windows", "3.12"),
        ]
    ]
    jobs = {
        "total_count": 7,
        "jobs": [
            {"name": n, "status": "completed", "conclusion": "success"} for n in names
        ],
    }
    artifact = {
        "id": 456,
        "name": "r03-candidate-" + SHA,
        "expired": False,
        "digest": "sha256:" + DIGEST,
        "workflow_run": {"id": 123, "head_sha": SHA, "head_branch": "main"},
    }
    return run, jobs, artifact


def test_successful_preparation_identity(
    pub: ModuleType,
    context_env: None,
    preparation: tuple[dict[str, Any], dict[str, Any], dict[str, Any]],
) -> None:
    pub.validate_preparation(pub.context(), *preparation, SHA)


@pytest.mark.parametrize(
    "problem",
    [
        "main",
        "source",
        "event",
        "workflow",
        "failed",
        "job",
        "job-count",
        "expired",
        "digest",
        "artifact-run",
        "artifact-name",
    ],
)
def test_wrong_preparation_never_reaches_upload(
    pub: ModuleType,
    context_env: None,
    preparation: tuple[dict[str, Any], dict[str, Any], dict[str, Any]],
    problem: str,
) -> None:
    run, jobs, artifact = preparation
    main = SHA
    if problem == "main":
        main = "c" * 40
    if problem == "source":
        run["head_sha"] = "c" * 40
    if problem == "event":
        run["event"] = "push"
    if problem == "workflow":
        run["path"] = ".github/workflows/ci.yml"
    if problem == "failed":
        run["conclusion"] = "failure"
    if problem == "job":
        jobs["jobs"][0]["conclusion"] = "failure"
    if problem == "job-count":
        jobs["total_count"] = 8
    if problem == "expired":
        artifact["expired"] = True
    if problem == "digest":
        artifact["digest"] = "sha256:" + "c" * 64
    if problem == "artifact-run":
        artifact["workflow_run"]["id"] = 999
    if problem == "artifact-name":
        artifact["name"] = "other"
    with pytest.raises(ValueError):
        pub.validate_preparation(pub.context(), run, jobs, artifact, main)


def test_new_tag_targets_exact_commit(
    pub: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    created = []

    def gh(path: str, **kwargs: Any) -> Any:
        if kwargs.get("method", "GET") == "POST":
            created.append(kwargs["data"])
            return {}
        return None

    monkeypatch.setattr(pub.remote, "gh", gh)
    pub.ensure_tag(SHA)
    assert created == [{"ref": "refs/tags/v0.1.0", "sha": SHA}]


def test_release_conflict_is_preserved(
    pub: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(
        pub.remote,
        "gh",
        lambda _path, **_kwargs: {
            "id": 1,
            "tag_name": "v0.1.0",
            "body": "unreviewed notes",
            "prerelease": False,
            "draft": False,
            "assets": [],
        },
    )
    with pytest.raises(ValueError):
        pub.ensure_release(tmp_path, "reviewed notes")


def test_partial_release_uploads_missing_without_clobber(
    pub: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    (tmp_path / "SHA256SUMS").write_bytes(b"checksums")
    (tmp_path / "release.json").write_bytes(b"record")
    calls = []
    state: dict[str, Any] = {
        "id": 1,
        "tag_name": "v0.1.0",
        "body": "notes",
        "prerelease": False,
        "draft": True,
        "assets": [{"id": 2, "name": "release.json", "size": 6}],
    }

    def gh(path: str, **kwargs: Any) -> Any:
        calls.append((path, kwargs))
        if kwargs.get("method") == "PATCH":
            state["draft"] = False
        return state

    monkeypatch.setattr(pub.remote, "gh", gh)
    monkeypatch.setattr(
        pub.remote,
        "gh_bytes",
        lambda path: b"record" if path.endswith("/2") else b"checksums",
    )

    def upload(*args: str) -> bytes:
        assert args[:3] == ("release", "upload", "v0.1.0") and "--clobber" not in args
        state["assets"].append({"id": 3, "name": "SHA256SUMS", "size": 9})
        return b""

    monkeypatch.setattr(pub.remote, "command", upload)
    pub.ensure_release(tmp_path, "notes")
    assert state["draft"] is False
    assert any(kw.get("method") == "PATCH" for _, kw in calls)


def test_manual_workflow_has_scoped_approval_and_no_build() -> None:
    workflow = yaml.load(
        (ROOT / ".github/workflows/publish.yml").read_text(), Loader=yaml.BaseLoader
    )
    assert set(workflow["on"]) == {"workflow_dispatch"}
    assert workflow["concurrency"]["cancel-in-progress"] == "false"
    assert workflow["permissions"] == {"contents": "read", "actions": "read"}
    jobs = workflow["jobs"]
    assert set(jobs) == {"inspect", "upload", "public-verify", "finalize"}
    assert (
        jobs["upload"]["environment"]
        == jobs["finalize"]["environment"]
        == "pypi-production"
    )
    assert jobs["upload"]["permissions"]["id-token"] == "write"
    assert jobs["finalize"]["permissions"]["contents"] == "write"
    assert "id-token" not in jobs["finalize"]["permissions"]
    assert jobs["finalize"]["needs"] == ["public-verify"]
    assert len(jobs["public-verify"]["strategy"]["matrix"]["include"]) == 6
    for name, job in jobs.items():
        if name != "upload":
            assert "id-token" not in job.get("permissions", {})
        for step in job["steps"]:
            if "uses" in step:
                assert len(step["uses"].split("@")[-1]) == 40
            run = step.get("run", "")
            assert "uv build" not in run and "--clobber" not in run
            if "uv publish" in run:
                assert name == "upload" and "--trusted-publishing always" in run
                assert step["if"] == "steps.stage.outputs.upload_needed == 'true'"


@pytest.mark.parametrize("kind", [".whl", ".gz"])
def test_public_install_uses_production_specifier_not_local_archive(kind: str) -> None:
    from test_distribution import install_arguments

    args = install_arguments(kind, Path("/private/original.whl"), public=True)
    assert args[0] == "enrama==0.1.0" and "/private/original.whl" not in args
    assert "https://pypi.org/simple" in args and "--no-cache" in args
    assert ("--only-binary" if kind == ".whl" else "--no-binary") in args


def test_inspection_never_creates_tag_or_release(
    pub: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def gh(_path: str, **kwargs: Any) -> Any:
        assert kwargs.get("method", "GET") == "GET"
        return [] if _path == "releases?per_page=100" else None

    monkeypatch.setattr(pub.remote, "gh", gh)
    pub.ensure_tag(SHA, create=False)
    pub.ensure_release(tmp_path, "notes", write=False)


def test_unconfirmed_assets_never_publish_draft(
    pub: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    (tmp_path / "SHA256SUMS").write_bytes(b"sums")
    state = {
        "id": 1,
        "tag_name": "v0.1.0",
        "body": "notes",
        "prerelease": False,
        "draft": True,
        "assets": [],
    }

    def gh(_path: str, **kwargs: Any) -> Any:
        assert kwargs.get("method", "GET") == "GET"
        return state

    count = []
    monkeypatch.setattr(pub.remote, "gh", gh)
    monkeypatch.setattr(pub.remote, "command", lambda *args: count.append(args))
    with pytest.raises(ValueError, match="confirm"):
        pub.ensure_release(tmp_path, "notes")
    assert len(count) == 1


def test_failed_public_matrix_blocks_finalization(
    pub: ModuleType, context_env: None, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("GITHUB_JOB", "finalize")
    monkeypatch.setenv("GITHUB_RUN_ID", "789")
    monkeypatch.setenv("GITHUB_RUN_ATTEMPT", "1")
    monkeypatch.setattr(
        pub.remote, "gh", lambda *args, **kwargs: {"jobs": [], "total_count": 0}
    )
    monkeypatch.setattr(
        pub, "ensure_tag", lambda _sha: pytest.fail("Tag must not be created")
    )
    with pytest.raises(ValueError):
        pub.finalize(pub.context(), tmp_path)


def test_retry_finds_existing_draft_without_creating_another(
    pub: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    draft = {
        "id": 1,
        "tag_name": "v0.1.0",
        "body": "notes",
        "prerelease": False,
        "draft": True,
        "assets": [],
    }

    def gh(path: str, **kwargs: Any) -> Any:
        if path == "releases/tags/v0.1.0":
            return None
        if path == "releases?per_page=100":
            return [draft]
        if kwargs.get("method") == "PATCH":
            draft["draft"] = False
            return draft
        pytest.fail("Unexpected operation: " + path)

    monkeypatch.setattr(pub.remote, "gh", gh)
    pub.ensure_release(tmp_path, "notes")
    assert draft["draft"] is False


@pytest.mark.parametrize("problem", [None, "provenance", "ci", "attempt"])
def test_original_bundle_end_to_end_gate(
    pub: ModuleType,
    context_env: None,
    source_candidate: tuple[Path, Path, str],  # noqa: F811 - imported pytest fixture
    preparation: tuple[dict[str, Any], dict[str, Any], dict[str, Any]],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    problem: str | None,
) -> None:
    source, _, sha = source_candidate
    original = tmp_path / "original"
    assert make_bundle(source_candidate, original).returncode == 0
    record = json.loads((original / "release.json").read_text())
    record.update(
        source_ref="refs/heads/main",
        run_id="123",
        run_attempt="1",
        source_ci={
            "databaseId": 999,
            "headSha": sha,
            "headBranch": "main",
            "event": "push",
            "workflowName": "CI",
            "status": "completed",
            "conclusion": "success",
        },
    )
    if problem == "provenance":
        record["run_id"] = "124"
    (original / "release.json").write_bytes(pub.release.canonical(record))
    content = {
        p.name: p.read_bytes() for p in original.iterdir() if p.name != "SHA256SUMS"
    }
    (original / "SHA256SUMS").write_bytes(pub.release.checksums(content))
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as z:
        for p in original.iterdir():
            z.writestr(p.name, p.read_bytes())
    data = stream.getvalue()
    digest = hashlib.sha256(data).hexdigest()
    run, jobs, artifact = preparation
    run["head_sha"] = sha
    if problem == "attempt":
        run["run_attempt"] = 2
    artifact.update(name="r03-candidate-" + sha, digest="sha256:" + digest)
    artifact["workflow_run"]["head_sha"] = sha

    def gh(path: str, **kwargs: Any) -> Any:
        assert kwargs.get("method", "GET") == "GET"
        if path == "actions/runs/123":
            return run
        if path.endswith("/jobs?per_page=100"):
            return jobs
        if path == "actions/artifacts/456":
            return artifact
        if path == "git/ref/heads/main":
            return {"object": {"sha": sha}}
        if path == "actions/runs/999":
            return {
                "head_sha": sha,
                "head_branch": "main",
                "event": "push",
                "path": ".github/workflows/ci.yml",
                "status": "completed",
                "conclusion": "failure" if problem == "ci" else "success",
            }
        if path == "releases?per_page=100":
            return []
        if path in {"git/ref/tags/v0.1.0", "releases/tags/v0.1.0"}:
            return None
        pytest.fail("Unexpected network operation: " + path)

    monkeypatch.setattr(pub.remote, "gh", gh)
    monkeypatch.setattr(pub.remote, "gh_bytes", lambda _path: data)
    monkeypatch.setattr(pub, "release_notes", lambda _c: "notes")
    monkeypatch.chdir(source)
    monkeypatch.setenv("GITHUB_SHA", sha)
    selected = pub.Context(sha, 123, 456, digest)
    output = tmp_path / "selected"
    if problem is not None:
        with pytest.raises(ValueError):
            pub.candidate(selected, output)
    else:
        pub.candidate(selected, output)
        assert {p.name: p.read_bytes() for p in output.iterdir()} == {
            p.name: p.read_bytes() for p in original.iterdir()
        }
