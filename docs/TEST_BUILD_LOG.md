# 0.1.0-test.1 — 19.10.2026

Status: **installed, native locale bootstrap observed; visual/runtime acceptance pending**. No stable release.

Payload SHA-256: `15ff3725d3dca7bd07073a6afbfb7ea632625117da030d41ea750c607d4c5e6c` (185663 bytes).
Original SHA-256: `f2e607c1a39377076913a4a04672139beaa514154499b9d024acccc07bfc3a96` (185662 bytes).
Exact final source commit is in the frozen local manifest and candidate source archive. The initial research commit was d72543ab6f3dcda4eacfd53bc7a593a120f8f976; metadata documentation initially said Python 3.13, then was corrected to observed Python 3.12.14 before user handoff. This correction does not change the locale payload bytes.

- Five original-tool tests pass; two independent build invocations on the original locale yield the payload SHA above, zlib runtime 1.3.2.
- Installed with game closed after verifying the original and payload SHA-256; verified exact backup outside the game assets and installed payload SHA-256.
- Relaunched host at 22:20:07 Moscow time. Log identifies application 2.58.17, Steam app 237990, locale ru; localeWranglerReadyHandler and BOOTSTRAPPED precede saga start page and completed load. No [ERROR] entries in sampled log.
- Raw session snapshot hash at observation: b28950fb589a623a47be34590bfc8b98a3a31bb98312458f78323006a9c9d59f. Raw log contains private machine identifiers and stays local, not in Git.
- Six save files before and after startup have identical SHA-256. This proves no change during this observed startup interval, not all future save compatibility.
- Window capture repeatedly timed out, including a retry after the user closed the baseline game. One separate attempt reported user input. The timeout cause is unknown; no screenshot or observed tooltip is claimed.
- User asked to check the red strength tooltip for the new sentence and clipping. Awaiting reply. Reverse installation procedure prepared; actual rollback/relaunch still pending because the host is open.

Candidate is installed; leave its identity intact while awaiting user evidence. Do not rebuild different payload bytes under this version or merge to stable merely because native loading succeeded.
