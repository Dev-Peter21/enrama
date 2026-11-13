# Enrama 0.1.0 publication record

Published and verified on **2026-11-02**:

- [Production PyPI 0.1.0](https://pypi.org/project/enrama/0.1.0/).
- [GitHub Release v0.1.0](https://github.com/Dev-Peter21/enrama/releases/tag/v0.1.0).
- Released source/tag: `73602dd85aca2cb02df607d9e815a1c76218b733` / `v0.1.0`.
- MIT license; Python 3.12–3.15; YAML `schema_version: 1`.

## Source and original candidate

[Main push CI #41355485718](https://github.com/Dev-Peter21/enrama/actions/runs/41355485718)
passed all seven jobs: **5,084 passed / 16 capability skips**, no failures/errors.
The six verification environments were Linux/Python 3.12–3.15, macOS/Python 3.12
and Windows/Python 3.12. Those disposable CI builds were not the release files.

[Preparation #41355780347](https://github.com/Dev-Peter21/enrama/actions/runs/41355780347),
attempt 1, built one canonical set and passed **18 supplied-archive consumers**
across the same six environments. Original artifact ID: `13103371200`.
ZIP SHA-256:
`be1bb16f76b9a7d9a9af7288f4dc12dd191ef5ae97dd9fde068bb494c99ffeb0`.
The original ZIP, extracted files, checksums and provenance were preserved locally
outside finite Actions retention; the original artifact expires on
`2027-01-30T22:10:34Z`.

## Actual production execution and recovery

The maintainer explicitly authorized that exact source/run/artifact/digest.
[Initial run #41483216493](https://github.com/Dev-Peter21/enrama/actions/runs/41483216493)
completed the Trusted Publishing upload after manual approval. Immediate
verification at 19:18:32 UTC reported incomplete public files, directly after
the uploads at 19:18:29/30 UTC. Subsequent actual downloads established both
original files complete and byte-identical, consistent with propagation delay.

[Recovery run #41509270070](https://github.com/Dev-Peter21/enrama/actions/runs/41509270070)
used the identical authorized identities and completed **all nine jobs**.
Production inspection found no missing files, so uv publishing was skipped;
no second upload/token exchange, rebuild, replacement or new version was used.
Two maintainer approvals are recorded for recovery/upload and matching
tag/GitHub Release finalization. The agent approved neither environment gate.

| Public consumer environment | Actual Python | Passed | Skipped |
| --- | --- | ---: | ---: |
| Linux | 3.12.15 | 2 | 0 |
| Linux | 3.13.17 | 2 | 0 |
| Linux | 3.14.9 | 2 | 0 |
| Linux | 3.15.1 | 2 | 0 |
| macOS | 3.12.15 | 2 | 0 |
| Windows | 3.12.15 | 2 | 0 |

Each environment installed the actual public wheel and sdist in clean consumers,
using production PyPI without a local-archive substitute. All **12 passed**,
with no failures/errors. Evidence includes help/version, init, valid YAML edits,
validation, minimal/bold CLI builds, full resolved distribution versions and
POSIX preview lifecycle checks. Windows does not execute the POSIX SIGINT preview
checks; zero skipped test cases does not imply that lifecycle was covered there.
Two additional clean public consumers passed locally on macOS.

All nine workflow artifact groups were downloaded and their ZIP digests verified.
JUnit/count/environment records agree with the exact source and actual consumers.
Reviewed release notes and the final tag target match the approved source.

## Verified public files

Actual PyPI wheel/sdist downloads and all five actual GitHub Release assets were
downloaded and compared byte-for-byte with the original candidate. Neither PyPI
archive is yanked. GitHub Release ID: `431888087`; published at
`2026-11-02T19:37:38Z`, with `draft: false` and `prerelease: false`.

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `enrama-0.1.0-py3-none-any.whl` | 62334 | `c72d2f59962c12d726de920a0f9f6c178718c97a8dbba8c22d0ca5e96a0f1dc9` |
| `enrama-0.1.0.tar.gz` | 47597 | `b57f1349c1e2624269c4abfbd63d0bd244719e7bcee39523537d31a05e69d9e5` |
| `enrama-v1.schema.json` | 6580 | `5fe008eee299a7e0a507ed58570181198cffa1dc0b1256b5010d41c22810d770` |
| `release.json` | 1037 | `483f148163252222195f1c29b6ec7d057e08abd42e16f76e259c7c026acc8d44` |
| `SHA256SUMS` | 349 | `7de299dfa30e2ca2954cac07b21c6a1114544647139983d5711f10c556c0a015` |

The original `release.json` keeps `publication_authorized: false`: it describes
preparation, and was not rewritten after publication. Later authorization is
recorded by the dispatch and environment approval events.

## Post-release documentation boundary

README, changelog, security/support and related active repository guides now
reflect the shipped state on develop. Historical design/implementation reports
retain their original dated scope. No runtime, version, dependency, workflow,
released tag, archive, release note body or public asset is changed by this update.

The published wheel/sdist and PyPI version description retain their original
embedded README/metadata, including preparation-era wording. Updating repository
Markdown does not alter those frozen contents. A future metadata correction must
travel in a separately reviewed new release, not a replacement 0.1.0 upload.
Any new packaging-CI artifacts from this documentation revision are disposable.

R03 remains open for maintainer acceptance and explicit closure/Done. The tested
client Pages recipe/deployment is R04, and final MVP acceptance is MVP01; neither
is established by publishing the generator. The visual editor remains 0.2 work.
