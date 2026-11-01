"""Offline publication gates: no test exchanges credentials or publishes files."""

import hashlib
import importlib
import io
import zipfile
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

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
