# Испытания кандидатов BannerSagaUI

## 0.1.0-test.2 — Ram hover, 20.10.2026

Status: **research candidate built and installed; AIR/runtime/UX-unaccepted**. Агент игру не запускал. Это ограниченная проба штатных стрелок «Тарана» по наведению до выбора цели; новый прогноз брони/силы и подпись стоимости не включены. При выбранной цели остаётся штатный путь подтверждения. Для первой пробы задан сценарий CANDIDATES.md; не применять способность на первом проходе.

- Exact source: `4a891e841555491f0490fe24dcfdf5c349737698`, ветка research/ui-clarity, VERSION `0.1.0-test.2`. Следующие изменения только документов не меняют эту идентичность.
- Payload: `BannerSagaUI-0.1.0-test.2-RamHover.swf`, 32513161 байт; ресурс назначения `win32/app.game-saga1.air.swf`.
- Payload/installed SHA-256: `ccb2918b8dd04d47e83261a4b210146904f85b13adebd6fb4110b3c4bc3597fa`.
- Original/backup SHA-256: `7d24a5910b9a0b3dfdae21443e3f0b7edd2510d6269d8407b6d0d31a5178a317`.
- Сборка `tools/build_ram_hover.py`: Python 3.12.14 stdlib, JRE 17.0.20.1+1, FFDec 26.4.0. Две независимые сборки из одного чистого source дали одинаковые байты. Исходный SWF в ходе сборок не менялся.
- Структурный контроль: сохранены заголовок кадра/версия, 3674 других тега, ABC-сигнатуры/константы/traits и 28897 из 28901 тел. Меняются только constructor/cleanup/onRender/checkCanRender AbilityDestinationOverlay: body indices 21637/21638/21641/21644. Локальные переменные, scope, исключения и traits тел прежние; единственное изменение лимита стека — onRender 6→9. Повторный FFDec-экспорт разработческого payload прочитан и просмотрен. Это не верификация AIR.
- 13 тестов оригинальных инструментов проходят; синтаксис сборщика проверен. Инструменты p-code/исследовательские экспорты и все бинарные результаты остаются вне Git. Сборочный manifest заморожен; факт установки хранится здесь отдельно от его исторического статуса на момент сборки.
- При закрытой игре перед установкой проверен исходный SWF и создана/проверена его отдельная резервная копия вне игры. После копирования проверен установленный payload hash. Прежняя локаль test.1 не заменялась и сохранила SHA-256 `15ff3725d3dca7bd07073a6afbfb7ea632625117da030d41ea750c607d4c5e6c`.
- После установки, до запрошенной пользовательской проверки, при закрытой игре снят локальный снимок хешей 11 файлов save/saga1. Это точка отсчёта следующего игрового сеанса, не свидетельство выполнения/сохранности будущих действий. Сохранения со стороны агента не записывались.

Не подтверждены: загрузка этого SWF в AIR, показ/переключение/очистка hover-стрелок, уход на HUD, возврат/подтверждение, регрессия обычной атаки и физический геймпад. Production/UX acceptance и stable promotion не получены. Откат test.2 — исходный SWF с указанным хешем при закрытой игре; предыдущую locale-пробу откатывать отдельно только по её задаче.

## История 0.1.0-test.1 — 19.10.2026

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
