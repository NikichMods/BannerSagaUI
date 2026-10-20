# 0.1.0-test.1 — 19.10.2026

## Дополнительное свидетельство штатного боевого UI, 20.10.2026

Получены шесть пользовательских кадров 2560×1440: расстановка, план перемещения, команды после движения, режим «Тарана», обычная атака и выбранная цель «Тарана» до применения. Исходные хеши/наблюдения/границы — COMBAT_EXAMPLES.md, оригиналы остаются только в игнорируемом local/evidence/ram-sequence-2026-10-20. Это новое свидетельство UX исходного пути, не новый кандидат, не тест после применения «Тарана» и не stable acceptance. Номер профиля и точная версия этого сеанса по кадрам не установлены. Агент игру/сохранения не менял.

## Идентичность и предыдущая проверка кандидата

Status: **installed, tooltip display verified by user screenshot; stable/UX acceptance pending**. No stable release.

Payload SHA-256: `15ff3725d3dca7bd07073a6afbfb7ea632625117da030d41ea750c607d4c5e6c` (185663 bytes).
Original SHA-256: `f2e607c1a39377076913a4a04672139beaa514154499b9d024acccc07bfc3a96` (185662 bytes).
Exact final handed source commit: dc703c0b0b32dba426a6c2b0ae717e8de277a27f, recorded in the final candidate manifest and source archive. The earlier research commit was d72543ab6f3dcda4eacfd53bc7a593a120f8f976; intermediate manifests initially said Python 3.13, then final metadata was corrected to observed Python 3.12.14 before user handoff. Intermediate manifests are historical, not the final source identity. This correction does not change the locale payload bytes.

- Five original-tool tests pass; two independent build invocations on the original locale yield the payload SHA above, zlib runtime 1.3.2.
- Installed with game closed after verifying the original and payload SHA-256; verified exact backup outside the game assets and installed payload SHA-256.
- Relaunched host at 22:20:07 Moscow time. Log identifies application 2.58.17, Steam app 237990, locale ru; localeWranglerReadyHandler and BOOTSTRAPPED precede saga start page and completed load. No [ERROR] entries in sampled log.
- Raw session snapshot hash at observation: b28950fb589a623a47be34590bfc8b98a3a31bb98312458f78323006a9c9d59f. Raw log contains private machine identifiers and stays local, not in Git.
- Six save files before and after startup have identical SHA-256. This proves no change during this observed startup interval, not all future save compatibility.
- Window capture repeatedly timed out, including a retry after the user closed the baseline game. One separate attempt reported user input. The timeout cause is unknown. Subsequently the user supplied a screenshot; see the later evidence below.
- User requested an isolated test save before gameplay. With host closed, profile 0 was cloned byte-for-byte into previously absent profile 1; all 5 copied files match and the original 6-file tree including master is unchanged. Separate backup ZIP SHA-256: c34e039ba4f77f43f040649410ac110401df2e3bf52baa68cd97c7029f0ad5b8. No save content is in Git. Subsequent runtime log confirms profile_index=[1] and a save to save/saga1/1/resume.save.json.
- Closed-file rollback to the original locale SHA and reinstall of the same candidate SHA were both verified. No runtime relaunch after rollback is claimed. At that historical checkpoint the candidate remained installed and host was left closed. Subsequent test evidence follows below.

Candidate is installed; leave its identity intact while awaiting user evidence. Do not rebuild different payload bytes under this version or merge to stable merely because native loading succeeded.

## Subsequent user test

- User screenshot SHA-256: 4d1cba93117cd7fc0611422c724ff7a153746ad499d14dcf1d7a42338cbaec67. Image retained only in ignored local/evidence, not published in Git.
- Screenshot shows Iver strength 12/12 and the complete candidate tooltip including the new sentence, with no visible clipping in the submitted image. It is one long single-line strip: layout improvement remains a separate proposal, not an accepted implementation.
- Current native log records GameConfig.loadSaga profile_index=[1], save_id=[resume], followed by save/saga1/1/resume.save.json. The test profile is loaded and used for autosave.
- All five original profile-0 files still match the pre-test backup SHA-256. Shared master/settings are outside this per-profile guarantee.
- This establishes real display and test-profile operation, not explicit user acceptance for stable promotion, general resolution coverage, or all tooltip consumers.
