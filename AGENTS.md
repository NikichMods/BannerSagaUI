# BannerSagaUI

Follow NikichMods/DevRules, beginning with WORKING_RULES.md and its action map; local checkout work also follows CODEX_WORKFLOW.md. This contract supplements those rules.

## Scope and evidence

The Banner Saga 1, Steam Windows, Russian UI clarity without rebalance. First inspected host: application 2.58.17, Steam build 3268685. Do not assume Factions or sequels share the current implementation. There is no separate shared host research repository yet.

Read docs/RESEARCH.md, docs/UI_AUDIT.md and docs/CANDIDATES.md before implementation. Inspect actual Git state and local unpublished changes. Host assets/decompiled code/saves stay outside Git, including private repositories. Commit derived facts, hashes and original tools only.

## Invariants

Preserve combat, progression, narrative uncertainty, saves, other languages and unrelated mods. Prefer existing data consumers over replacing SWF code. Each independent behavior needs the DevRules READY gate. A full locale-file hash guard is intentional for the first experiment: it prevents replacing another mod's shared locale file before coexistence is researched.

## Versions and acceptance

main is stable; research/* holds research and unaccepted candidates. VERSION is the sole candidate version owner. Numbered handed artifacts are immutable, tied to the exact committed source and SHA-256. Runtime acceptance requires the user to see the changed Russian tooltip, verify legibility, preserved behavior and rollback. Do not promote static parsing/build success to runtime acceptance or publish a stable release before that acceptance.

Build with Python 3.13 standard library: python tools/build.py --game-root <path> --out <empty-directory>. Test with python -m unittest discover -s tests. No host payload in distributed source bundles. Installation is a separate closed-game operation with verified backup and installed hash. No automated save edits or game termination.

Original software is MPL-2.0; see LICENSING.md. No exception to DevRules.
