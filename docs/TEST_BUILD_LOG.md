# Испытания кандидатов BannerSagaUI

## Отказ test.3 и восстановление DEV — 20.10.2026

Пользователь сообщил о неподвижном экране и отсутствии реакции после входа в тренировочный бой. Завершённый DEV-журнал, 20788 байт, SHA-256 `c9e0a31476315f513f3a98f699e53df9ec5a0a23030c3ede315f4e0b2bc328c8`, подтверждает RU, profile_index=1, тренировочную доску и `VerifyError: Error #1030` в стеке `BattleAbilityManager.onAbilityFinalComplete`. Ошибка возникает при первом `pas_returnthefavor/1` Ивера, до выбора «Тарана». Записей BSUI_RAM_PROBE/BSUI_RAM_IDLE нет: числовое сравнение не состоялось. Последующий штатный выход записан; агент процесс не завершал. Установленный хеш на момент разбора совпал с DEV/test.3 ниже. Сырые свидетельства — ignored local; пути в local/RESUME.md.

При закрытой игре восстановлена проверенная пара прежнего DEV-SWF и точного dev-manifest.json из предустановочного бэкапа. Текущий установленный SHA-256 `b01dd6538606bfb69e0f2b41b82b8d69766f7cc5b27f039aaa962a13555c359c` — test.2 + отдельная SteamEntry-адаптация. CheckOnly прошёл, игра агентом не запускалась. Все 12 файлов личных сохранений/настроек и все 12 DEV-файлов совпали с предустановочными хешами; неудачный сеанс и откат их содержимое не изменили. Локаль/дескриптор/INI не менялись.

Статический разбор обнаружил несовместимые высоты стека в донорском probe.pcode ещё до трансплантации и те же дефекты после неё. Тело менеджера само по этой ограниченной проверке сбалансировано; кадр менеджера в stack trace не устанавливает, что ошибка находится именно в нём. Удаление только вложенного finally проблему не сняло. Вынос очистки в общий участок после catch-all устраняет выявленные несогласованности; новая неномерная сборка проверяется отдельно, test.3 не переписывается и не считается исправленным. Механизм и предел вывода — RESEARCH.md. Структурные проверки прежнего сборщика и 21 тест не заменили AIR-verifier; добавлены проверка высоты стека и пять синтетических регрессий. Полный набор из 26 тестов прошёл вне песочницы; внутри неё прежние пять файловых тестов опять получили PermissionError временных каталогов.

## 0.1.0-test.3 — заморозка и установка диагностического расчёта, 20.10.2026

**Историческая установка; отозвана и откачена, текущая DEV-среда описана выше.**

Exact source `a3fd5cea66414f13aef4176c0be2291387570ab3`, чистый commit с VERSION=0.1.0-test.3. Две независимые сборки из проверенного оригинала совпали: `BannerSagaUI-0.1.0-test.3-RamForecastProbe.swf`, 32516964 байта, SHA-256 `ea44c981df6749513f2a61bfd9e43746a895b692ec9e72f5287b00177c8f51e2`. Номерной артефакт/манифест не меняются последующими коммитами документации. Сборка: Python 3.12.14, Java 17.0.20.1+1, FFDec 26.4.0; `python tools/research/build_ram_probe.py --game-root <оригинальная-база> --java <java.exe> --ffdec <ffdec-cli.jar> --out <новый-каталог> --freeze`.

Все 21 тест инструментов проходят. Первый запуск в песочнице снова получил известный PermissionError у пяти файловых тестов TemporaryDirectory; тот же набор вне песочницы прошёл, тестовый код не менялся ради обхода. Синтетические проверки анализатора покрывают совпадение/несовпадение, отмену, неподдержанный случай, нарушение инварианта, незавершённый журнал и чужую цель; они не доказывают игровые числа.

Структурно изменены ровно 6 тел ABC tag3671: 2613/getStatChange, 13298/onAbilityFinalComplete и прежние четыре hover-тела 21637/21638/21641/21644. Остальные 28895 тел побайтово прежние; число методов/тел, method_info, class/script traits, metadata и прежние записи constant pools сохранены. Повторный p-code экспорт подтвердил сохранность инструкций и двух exception regions штатной ветки getStatChange. Это статические проверки, не AIR-verifier/runtime. Диагностическая ветка не является новым общим getStatChange для «Тарана»; механизм/ограничения — RESEARCH.md.

Для DEV отдельно повторно применён прежний SteamEntryHelper.processArgument (body599/method612). От кандидата отличается только это тело, его metadata прежние; адаптированное тело побайтово совпало с прежним DEV. Установленный составной SHA-256 `e0e15e2ffcd5b1233e12298e1622ab491667dbbe385cb5d7e8dac7e588f35616`, 32516964 байта. **Это другой файл, не payload под старым хешем кандидата.**

Установка выполнена при закрытой игре; все 7 прежних проверок хешей запускателя предварительно совпали. Предыдущий DEV-SWF `b01dd6538606bfb69e0f2b41b82b8d69766f7cc5b27f039aaa962a13555c359c` и точный старый dev-manifest.json сохранены/сверены вне загрузочного каталога; машинный путь отката — local/RESUME.md. После установки сверён хеш назначения, обновлён только соответствующий launch_file_hash и идентичность текущего кандидата; прежняя runtime-проверка в манифесте помечена прежним хешем, current runtime_verified=false. Launch-Dev.ps1 -CheckOnly прошёл без запуска игры. До/после совпали хеши всех 12 учитываемых файлов личного хранилища и 12 файлов DEV; автоматического редактирования сохранений/завершения/запуска игры не было. Локаль, AIR-дескриптор и INI не менялись.

Первый пользовательский runtime завершился отказом, описанным выше; числовое совпадение, восстановление fake-режима в AIR и UX-приёмка не доказаны. Прогноз UNVERIFIED и настоящий исход предполагалось сопоставлять по BSUI_RAM_PROBE / BSUI_RAM_IDLE после реального Execute того же caster/target/ранга. Исправленный кандидат должен иметь новый номер; test.3 остаётся неизменяемым свидетельством неудачной пробы.

## Первая проверка геймпада в DEV — 20.10.2026

**Уточнение пользователя после проверки:** штатный выбор целей действительно работает через крестовину влево/вправо. Управление в целом оценено как неудобное; принято продолжать с клавиатурой/мышью и короткой регрессией геймпада. Его переработка отложена отдельно; настройка кнопок не утверждена. Это подтверждает привязку/перебор, но не отдельный полный проход подтверждения/выполнения/отмены и не приёмку всего геймпадного UX. Ниже — первоначальное затруднение и диагностический шаг, уже выполненный пользователем.

Пользователь сообщил: после выбора «Тарана» видны фиолетовые клетки и одна более яркая, пути/подтверждения нет, B возвращает назад; применить способность не удалось. Скриншот подтверждает это состояние экрана, но не последовательность нажатий. Не считать геймпад принятым или регрессию доказанной.

Сохранён завершённый DEV-журнал (22840 байт, SHA-256 `c0e3a4f7a1787a2afe3290fb1496af55587c2c655335c70e16d2a6d3231f990e`): RU, null steamworks, profile_index=1, тренировочный бой, движение Ивера, переключения global.gp, штатный выход. Две ERROR относятся к news/audio; типичных исключений исполнения не найдено. Журнал не фиксирует кнопки/targetSet и не устанавливает причину затруднения. Установленный SWF сверён: прежний составной DEV `b01dd6538606bfb69e0f2b41b82b8d69766f7cc5b27f039aaa962a13555c359c`. Raw-журнал/скриншот — ignored local/evidence/ram-hover-dev-gamepad-2026-10-20.

Повторно просмотрен штатный BattleHudPageInput: D_L/D_R → _findInteract → getInteractIndex_ability (кандидаты из turn._inRange) → _processInteract → handleAbilityClick; A → handleTileSelect_local → штатный путь подтверждения. Новая targetless-hover ветка test.2 намеренно исключает lastInputGp. Следующая короткая проверка: выбрать «Таран», нажать крестовину влево/вправо и проверить появление выбранной цели/пути/подтверждения; затем B. Яркая клетка сама по себе не доказывает выбранную цель. Если этот штатный путь не сработает, потребуется отдельная диагностика; производственные изменения пока не обоснованы.

## Рабочая среда DEV — 20.10.2026

**Принята как основная среда следующих рабочих установок и испытаний.** Это не новая версия мода и не stable promotion. Дальнейший порядок — DEVELOPMENT_ENVIRONMENT.md; личная Steam-установка не является рабочей целью. Все упомянутые ниже raw-файлы/манифесты остаются локальными; местоположение — local/RESUME.md.

Скопированы и сверены SHA-256 всех 9797 игровых файлов (3335672484 байта), затем в копии отдельно изменены SWF, AIR-дескриптор и INI, добавлен собственный запускатель. Исходная личная установка не изменялась в ходе подготовки DEV. База — SWF test.2 `ccb2918b8dd04d47e83261a4b210146904f85b13adebd6fb4110b3c4bc3597fa`; локальная настройка SteamEntryHelper даёт установленный составной SHA-256 `b01dd6538606bfb69e0f2b41b82b8d69766f7cc5b27f039aaa962a13555c359c`. Метаданные/остальной SWF сохранены; технический seam — RESEARCH.md. Неизменяемый test.2 ниже не пересобирался и не переименовывался в этот файл.

Первый пользовательский запуск выявил CR в значениях переписанного CRLF-конфига: локаль/кампания не загрузились, игра завершилась. Исправлен только формат INI на LF, записаны прежние исходные значения и параметры запуска. Хеш снимка неуспешного журнала `3f354d528c804335c267bef382f98cfe59bc6a5bc8006b87be619cb427833f05`. Точный механизм/предотвращение повтора — RESEARCH.md.

**Успешный меню-сеанс 14:20:16 МСК:** пользователь дошёл до меню и вышел. Журнал подтвердил русский язык, assets из DEV-копии, хранилище TheBannerSagaDev, Enabling null steamworks, пропуск облачного чтения/записи, готовность меню и Quit from Start Menu → exitTimerCompleteHandler. ERROR/типичных исключений в этом снимке нет; SHA-256 журнала `8a43e592e0ea3e59db3b653cf79e3a573e0ca384196af599ea57904626328410`. Все 11 исходных сохранений и настройки совпали с предкопировочными хешами; все 12 DEV-файлов физически отдельны, symlink/junction в проверенных деревьях не найдены. Меню могло обновлять метки времени локальных master/settings при прежнем содержимом — не считать это записью в исходные файлы.

**Совместный сеанс с открытым Steam 14:27:40 МСК, около 231 с:** клиент версии 1791918634 вошёл в нужный аккаунт до начала замера. Наблюдались отдельный рабочий процесс из DEV-каталога и тот же работающий Steam. Во время сеанса Steam registry Running для app 237990 оставался 0; пользователь также не видел игру в списке запущенных. До, во время и после сеанса локальные Playtime/Playtime2wks, LastPlayed и LastPlayed appmanifest не изменились: прирост времени 0 минут. Полный хеш gameprocess_log не изменился, новый процесс к app 237990 не добавлялся. Игра подтвердила null Steamworks и штатно закрылась через меню. В журнале есть отказ загрузки новостей, без ошибки загрузки локали/кампании; такой тип news-ошибки наблюдался до DEV и не свидетельствует о сбое Steam-bypass.

| Локальное свидетельство совместного сеанса | SHA-256 |
|---|---|
| before.json | `f842416c48788442bd9d6353352aefda80b2ab2e4c092405ddaaa3f5ec915b6c` |
| during.json | `c9ddeec508c5750092b4e091e65d0af3497e7501408768ae53da27ef2891ca15` |
| after.json | `4ad0b416eb727682b7bfa5573e548a4ab251763e4184a6b46ee54dd33f4f12ae` |
| A-0.completed.log.txt, 10376 байт | `86b013839b9ce22f715dead2f20762ab8ba375c1b91be4c948d0e8d7436d7804` |

После этой проверки удалён только запрет открытого Steam из основного запускателя; integrity-проверки и запрет второго экземпляра сохранены. CheckOnly прошёл с открытым Steam без запуска игры. Временный прямой тестовый ярлык убран из корня рабочей папки и сохранён вместе со свидетельствами; основной ярлык остаётся единственным обычным способом запуска.

Граница вывода: проверены локальные счётчики/отслеживание текущего клиента, без независимого серверного запроса; меню, не бой/физический геймпад. Это не полная приёмка модифицированного UI и не перенос результата на TBS2/TBS3 или любую будущую версию Steam/AIR. При изменении интеграции/базы/способа запуска повторить нужную проверку. Личная установка и её история испытаний test.2 ниже сохранены как история.

## 0.1.0-test.2 — Ram hover, 20.10.2026

Status: **installed; user reports hover/cleanup working; startup/training session verified in log; broader acceptance pending**. Агент игру не запускал. Это ограниченная проба штатных стрелок «Тарана» по наведению до выбора цели; новый прогноз брони/силы и подпись стоимости не включены. При выбранной цели остаётся штатный путь подтверждения. Для первой пробы задан сценарий CANDIDATES.md; не применять способность на первом проходе.

- Exact source: `4a891e841555491f0490fe24dcfdf5c349737698`, ветка research/ui-clarity, VERSION `0.1.0-test.2`. Следующие изменения только документов не меняют эту идентичность.
- Payload: `BannerSagaUI-0.1.0-test.2-RamHover.swf`, 32513161 байт; ресурс назначения `win32/app.game-saga1.air.swf`.
- Payload/исторический installed SHA-256 личной Steam-установки: `ccb2918b8dd04d47e83261a4b210146904f85b13adebd6fb4110b3c4bc3597fa`. Текущая DEV-композиция имеет отдельный хеш в разделе выше.
- Original/backup SHA-256: `7d24a5910b9a0b3dfdae21443e3f0b7edd2510d6269d8407b6d0d31a5178a317`.
- Сборка `tools/build_ram_hover.py`: Python 3.12.14 stdlib, JRE 17.0.20.1+1, FFDec 26.4.0. Две независимые сборки из одного чистого source дали одинаковые байты. Исходный SWF в ходе сборок не менялся.
- Структурный контроль: сохранены заголовок кадра/версия, 3674 других тега, ABC-сигнатуры/константы/traits и 28897 из 28901 тел. Меняются только constructor/cleanup/onRender/checkCanRender AbilityDestinationOverlay: body indices 21637/21638/21641/21644. Локальные переменные, scope, исключения и traits тел прежние; единственное изменение лимита стека — onRender 6→9. Повторный FFDec-экспорт разработческого payload прочитан и просмотрен. Это не верификация AIR.
- 13 тестов оригинальных инструментов проходят; синтаксис сборщика проверен. Инструменты p-code/исследовательские экспорты и все бинарные результаты остаются вне Git. Сборочный manifest заморожен; факт установки хранится здесь отдельно от его исторического статуса на момент сборки.
- При закрытой игре перед установкой проверен исходный SWF и создана/проверена его отдельная резервная копия вне игры. После копирования проверен установленный payload hash. Прежняя локаль test.1 не заменялась и сохранила SHA-256 `15ff3725d3dca7bd07073a6afbfb7ea632625117da030d41ea750c607d4c5e6c`.
- После установки, до запрошенной пользовательской проверки, при закрытой игре снят локальный снимок хешей 11 файлов save/saga1. Это точка отсчёта следующего игрового сеанса, не свидетельство выполнения/сохранности будущих действий. Сохранения со стороны агента не записывались.

### Первый пользовательский проход и журнал

Пользователь сообщил, что выполнил предложенный сценарий: путь до клика появляется, всё правильно очищается, видимых проблем не заметил. Это положительное свидетельство работы/восприятия в проверенном сценарии; новой серии кадров или наблюдения агента нет. Каждое подусловие отдельно и физический геймпад не заявлены как независимо проверенные. Stable promotion этим не запрошен.

Сеанс процесса начат 20.10.2026 в 12:26:22 МСК, после установки кандидата. Снимок текущего TBS1 A-0.log.txt снят при открытой игре 12:32:16 МСК; 39749 байт, SHA-256 `c59cead12f347fd860b32d19804e65da1354423e897af97ccdb3b908504643ab`. Сырые данные остаются в local; будущий хвост сеанса в снимок не входит. На момент чтения установленный SWF всё ещё имеет payload hash test.2. Журнал подтверждает 2.58.17, locale ru, BOOTSTRAPPED, загрузку resume с profile_index=1, тренировочный бой btl_training, первый ход Ивера и выполненное перемещение. Лог не содержит собственного идентификатора нашей версии или каждого hover-события: связь с кандидатом основана также на порядке установки/старта, установленном хеше и характерном наблюдении пользователя.

В снимке 3 строки ERROR и 0 WARN: два отказа загрузки news1.json и одна проблема SceneAudioEmitterAudible с 3D-позицией фонового звука. Такие же типы news/audio-ошибок присутствуют в предыдущем A-1.log.txt до test.2; признаков связи с изменённым слоем не найдено, точная причина не исследовалась. VerifyError/TypeError/ReferenceError/RangeError/SecurityError/ArgumentError в снимке не обнаружены. Отсутствие этих сообщений не является доказательством всех инвариантов интерфейса или отсутствия любых ошибок вне снимка.

После прохода повторно прочитаны все 11 файлов из предтестового снимка save/saga1: хеши совпали, в том числе все 5 файлов оригинального профиля 0. Это наблюдение в указанный момент, не гарантия неизменности при дальнейшем игровом прогрессе; агент сохранения не записывал.

Остаются ранний физический геймпад и представительская регрессия соседних режимов; расширенная UX-приёмка/stable promotion не получены. Откат test.2 — исходный SWF с указанным хешем при закрытой игре; предыдущую locale-пробу откатывать отдельно только по её задаче.

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
