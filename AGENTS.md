# BannerSagaUI

Follow NikichMods/DevRules, beginning with WORKING_RULES.md and its action map; local checkout work also follows CODEX_WORKFLOW.md. This contract supplements those rules.

## Scope and evidence

The Banner Saga 1, Steam Windows: systematic UI/UX audit leading to an agreed set of improvements, with Russian as the first verified locale and no rebalance. Substantial screen/layout/interaction redesign is permitted when justified; preserve the artistic style without preserving inconvenient layout by default. First inspected host: application 2.58.17, Steam build 3268685. There is no separate shared host research repository yet.

Derive product goals from the broad audit, not from the first technically easy patch. Include current TBS2/TBS3, official changes, professional criticism and direct player reports as comparative evidence. Do not assume later means better, a historical complaint remains current, or shared engine/class names prove compatibility. Check official backports before proposing one. See docs/UI_SOURCES.md and docs/SEQUEL_COMPARISON.md. User-owned sequel installations/assets are authorized research inputs; that does not settle distributable payload rights or permit game-owned content in Git.

Start with docs/PROJECT.md for the goal, current position, open decisions and next-step rationale. Then read task-relevant sections of docs/PROBLEM_CATALOGUE.md, docs/RESEARCH.md, docs/UI_AUDIT.md, docs/CANDIDATES.md and docs/TEST_BUILD_LOG.md before implementation. Inspect actual Git state and local unpublished changes. Host assets/decompiled code/saves stay outside Git, including private repositories. Commit derived facts, hashes and original tools only.

## Project continuity

Reusable engine/tooling knowledge is a parallel support task for this mod and later trilogy work. Use docs/ENGINEERING_GUIDE.md as the practical entry point, with evidence kept in its owning research/test documents. Preserve findings that change a decision or avoid repeated work; do not require a daily/transcript log. Mark each result's verified game/build and evidence level; do not infer trilogy compatibility. Publish only original tooling and derived knowledge; private Git is not an exception for host-owned materials. This support work must help, not replace, delivery of the mod.

Maintain docs/PROJECT.md as the single current project map. At meaningful research, design or test boundaries, connect the result to the overall UI-clarity goal: what became known, what remains uncertain, which materially different options remain, and what next action is justified by the evidence. Explain important choices and their consequences in concise user-facing rationale; do not report only the latest isolated operation. Scale this to the decision; do not repeat the entire map after routine checks.

Keep adopted decisions distinct from recommendations and hypotheses. Update the owning evidence/test documents and the affected current-map claims within the same working segment; do not create a transcript ledger or duplicate technical evidence. At resume, recover from the map and actual files; at handoff, preserve the smallest missing state and a concrete next step. Runtime proof, UX acceptance and stable promotion remain separate.

## Invariants

Preserve combat, progression, narrative uncertainty, saves, other languages and unrelated mods. Prefer existing data consumers over replacing SWF code. Each independent behavior needs the DevRules READY gate. A full locale-file hash guard is intentional for the first experiment: it prevents replacing another mod's shared locale file before coexistence is researched.

## Development runtime

Use the approved separate TBS1 development copy for subsequent mod installation, launches, logs and runtime tests; do not default to the personal Steam installation or its saves. See docs/DEVELOPMENT_ENVIRONMENT.md; machine paths and local manifests are in ignored local/RESUME.md. The development copy uses AIR application ID TheBannerSagaDev, independent save/settings files and the verified steam=false path. Steam may remain open on the tested configuration. Direct battle startup is not configured.

Keep the development Steam bypass separate from the mod candidate: build the immutable candidate from a verified original input, preserve/reapply the separately verified development adaptation for local installation, record both hashes and update the launcher's integrity manifest only after verification. Do not overwrite the development SWF with a plain candidate or call the adapted file the unchanged numbered artifact. Close the target game before installation; use its own verified backup for rollback. Personal-game installation and Steam-connected acceptance require a separate explicit task. Development-menu startup does not accept combat UX or a stable release.

## Versions and acceptance

main is stable; research/* holds research and unaccepted candidates. VERSION is the sole candidate version owner. Numbered handed artifacts are immutable, tied to the exact committed source and SHA-256. Runtime acceptance requires the user to see the changed Russian tooltip, verify legibility, preserved behavior and rollback. Do not promote static parsing/build success to runtime acceptance or publish a stable release before that acceptance.

Build with Python standard library (verified 3.12.14): python tools/build.py --game-root <path> --out <empty-directory>. Test with python -m unittest discover -s tests. No host payload in distributed source bundles. Installation is a separate closed-game operation with verified backup and installed hash. No automated save edits or game termination.

Original software is MPL-2.0; see LICENSING.md. No exception to DevRules.
