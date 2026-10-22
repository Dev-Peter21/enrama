# Published MVP backlog

The [EnRama Project Kanban](https://github.com/users/Dev-Peter21/projects/5)
tracks the path from repository initialization to the `0.1.0` MVP.
See all [MVP issues](https://github.com/Dev-Peter21/enrama/issues?q=is%3Aissue%20label%3Amvp)
and the [five milestones](https://github.com/Dev-Peter21/enrama/milestones).

Issue bodies contain scope, acceptance criteria, validation expectations, and
prerequisites. Dependencies are recorded as native GitHub blocked-by relationships
as well as links in the issue text. The [roadmap](roadmap.md) remains the product
planning specification; use the issue and Project for current execution status.

## Issue index

| Milestone | Task | Issue |
| --- | --- | --- |
| M0 — Foundation | F00: Repository and documentation initialization | [#1](https://github.com/Dev-Peter21/enrama/issues/1) |
| M0 — Foundation | F01: CLI and filesystem contract | [#2](https://github.com/Dev-Peter21/enrama/issues/2) |
| M0 — Foundation | F02: Python packaging and development tooling | [#3](https://github.com/Dev-Peter21/enrama/issues/3) |
| M0 — Foundation | F03: Foundation CI | [#4](https://github.com/Dev-Peter21/enrama/issues/4) |
| M1 — Configuration | C01: Version 1 models and field policy | [#5](https://github.com/Dev-Peter21/enrama/issues/5) |
| M1 — Configuration | C02: Safe YAML loading and actionable errors | [#6](https://github.com/Dev-Peter21/enrama/issues/6) |
| M1 — Configuration | C03: Generated schema and editor instructions | [#7](https://github.com/Dev-Peter21/enrama/issues/7) |
| M2 — Static Generator | G01: Safe asset resolution and copying | [#8](https://github.com/Dev-Peter21/enrama/issues/8) |
| M2 — Static Generator | G02: Template rendering and metadata | [#9](https://github.com/Dev-Peter21/enrama/issues/9) |
| M2 — Static Generator | G03: Safe, repeatable builds | [#10](https://github.com/Dev-Peter21/enrama/issues/10) |
| M3 — CLI & Themes | U01: Init, validate, and build commands | [#11](https://github.com/Dev-Peter21/enrama/issues/11) |
| M3 — CLI & Themes | U02: Local preview | [#12](https://github.com/Dev-Peter21/enrama/issues/12) |
| M3 — CLI & Themes | U03: Minimal theme and controlled icon catalog | [#13](https://github.com/Dev-Peter21/enrama/issues/13) |
| M3 — CLI & Themes | U04: Bold theme | [#14](https://github.com/Dev-Peter21/enrama/issues/14) |
| M4 — Public Release | R01: Example and end-to-end documentation | [#15](https://github.com/Dev-Peter21/enrama/issues/15) |
| M4 — Public Release | R02: Release validation | [#16](https://github.com/Dev-Peter21/enrama/issues/16) |
| M4 — Public Release | R03: First Python release | [#17](https://github.com/Dev-Peter21/enrama/issues/17) |
| M4 — Public Release | R04: Verified GitHub Pages client recipe | [#18](https://github.com/Dev-Peter21/enrama/issues/18) |
| M4 — Public Release | MVP01: Final end-to-end acceptance | [#19](https://github.com/Dev-Peter21/enrama/issues/19) |

## Kanban conventions

- **Backlog:** planned work, including tasks waiting for prerequisites or decisions.
- **Ready:** dependencies are satisfied and the next work is clear. Initial
  contract task F01 can start by resolving its documented decisions.
- **In progress:** someone is actively working on the agreed scope.
- **In review:** implementation and evidence are ready for review.
- **Done:** acceptance criteria are verified and the issue is completed.

At backlog publication, F00 is closed/Done with evidence of the initial commit;
F01 is Ready; all other issues are open/Backlog. MVP work has Priority P1;
the historical F00 record has P2. No assignees, delivery dates, or effort
estimates are imposed. Status changes should reflect actual progress.

## Publication verification

The initial publication encountered a mismatch between individual Project
memberships and the Project listing. On 2026-10-22, the existing issues were
reattached through GitHub's repository item selector, with their saved fields
restored. The board and aggregate listing now contain all 19 original issues.

Verification confirmed exactly one Project association per issue, 17 Backlog
cards, one Ready card, and one Done card. Issue numbers, open/closed states,
priorities, five milestones, and 32 native dependency relationships were
preserved. No duplicate issues or additional projects were created.

## Completion and scope

Do not mark the MVP complete until [#19](https://github.com/Dev-Peter21/enrama/issues/19)
contains evidence for every product acceptance criterion, including package
installation, both themes, security regression coverage, and static deployment.
Publication and deployment retain their explicit authorization gates.

The local visual editor (M5 / 0.2) remains documented in the roadmap, with no
MVP issue or milestone created for it. This backlog publication adds planning
and traceability only; it does not implement the product.
