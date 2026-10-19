# BannerSagaUI

Follow NikichMods/DevRules, beginning with WORKING_RULES.md and its action map; local checkout work also follows CODEX_WORKFLOW.md. This contract supplements those rules.

## Scope and evidence

The Banner Saga 1, Steam Windows, Russian UI clarity without rebalance. First inspected host: application 2.58.17, Steam build 3268685. Do not assume Factions or sequels share the current implementation. There is no separate shared host research repository yet.

Start with docs/PROJECT.md for the goal, current position, open decisions and next-step rationale. Then read task-relevant sections of docs/RESEARCH.md, docs/UI_AUDIT.md, docs/CANDIDATES.md and docs/TEST_BUILD_LOG.md before implementation. Inspect actual Git state and local unpublished changes. Host assets/decompiled code/saves stay outside Git, including private repositories. Commit derived facts, hashes and original tools only.

## Project continuity

Maintain docs/PROJECT.md as the single current project map. At meaningful research, design or test boundaries, connect the result to the overall UI-clarity goal: what became known, what remains uncertain, which materially different options remain, and what next action is justified by the evidence. Explain important choices and their consequences in concise user-facing rationale; do not report only the latest isolated operation. Scale this to the decision; do not repeat the entire map after routine checks.

Keep adopted decisions distinct from recommendations and hypotheses. Update the owning evidence/test documents and the affected current-map claims within the same working segment; do not create a transcript ledger or duplicate technical evidence. At resume, recover from the map and actual files; at handoff, preserve the smallest missing state and a concrete next step. Runtime proof, UX acceptance and stable promotion remain separate.

## Invariants

Preserve combat, progression, narrative uncertainty, saves, other languages and unrelated mods. Prefer existing data consumers over replacing SWF code. Each independent behavior needs the DevRules READY gate. A full locale-file hash guard is intentional for the first experiment: it prevents replacing another mod's shared locale file before coexistence is researched.

## Versions and acceptance

main is stable; research/* holds research and unaccepted candidates. VERSION is the sole candidate version owner. Numbered handed artifacts are immutable, tied to the exact committed source and SHA-256. Runtime acceptance requires the user to see the changed Russian tooltip, verify legibility, preserved behavior and rollback. Do not promote static parsing/build success to runtime acceptance or publish a stable release before that acceptance.

Build with Python standard library (verified 3.12.14): python tools/build.py --game-root <path> --out <empty-directory>. Test with python -m unittest discover -s tests. No host payload in distributed source bundles. Installation is a separate closed-game operation with verified backup and installed hash. No automated save edits or game termination.

Original software is MPL-2.0; see LICENSING.md. No exception to DevRules.
