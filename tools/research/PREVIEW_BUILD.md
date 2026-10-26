# Исследовательская основа полевых чисел TBS1

Только TBS1 Windows 2.58.17, исходный SWF SHA-256 `7d24a5910b9a0b3dfdae21443e3f0b7edd2510d6269d8407b6d0d31a5178a317`. Это отдельный исследовательский маршрут; основной `tools/build.py` остаётся на Python stdlib. Скрипты ничего не устанавливают и не запускают.

## Входы и сборка

Нужны имеющиеся у исследователя FFDec **26.4.0**, Java **17**, Python **3.12.14** и отдельный исследовательский JPype1 **1.6.0** (`pip --target` в ignored local). JPype соединяет Python с уже установленным Java API FFDec; игре и распространяемому моду он не требуется. Зависимости и AIR runtime не входят в Git. Изменение версии инструмента требует новой проверки, а не молчаливой подстановки.

```text
python tools/research/compile_preview.py --host <original.swf> --ffdec <ffdec-directory> --jvm <jvm.dll> --jpype-dir <private-jpype-directory> --out <empty-output> --mode contract-tests
python tools/research/compile_preview.py --host <original.swf> --ffdec <ffdec-directory> --jvm <jvm.dll> --jpype-dir <private-jpype-directory> --out <another-empty-output> --mode native-module
python tools/research/build_field_preview.py --game-root <original-game-root> --java <java.exe> --ffdec <ffdec-cli.jar> --module-dir <native-module-output> --out <new-output>
```

`compile_preview` создаёт пустой ABC и компилирует туда только собственные классы. Оригинальная игра служит таблицей типов; её классы не пересобираются. Импорты дополнительно сверяются с ABC игры: FFDec может скомпилировать неразрешённое имя без ошибки. Эта проверка подтверждает наличие классов, но не все свойства/права доступа/семантику AVM2.

Генератор провайдера переиспользует единственный project-owned `ram_probe_body.as.inc`: убирает диагностические вход/выход и выдаёт объект после cleanup. Участок расчёта и восстановления должен оставаться текстово идентичным после удаления трёх дополнительных полей snapshot. Штатные формулы не переписываются. Старые боевые guard сохраняются.

`build_field_preview` добавляет отдельный DoABC после native ABC и два вызова ScenePage: в конце успешного update, после штатных ранних выходов, и в начале cleanup после установки scope. Сохраняет четыре прежних изменения Ram-hover, но не добавляет старые sentinel/getStatChange/idle-hook. Новые имена добавляются в pools; старые записи, сигнатуры, traits и все другие тела проверяются. Проверяется неизменность собственного ABC после импорта hooks и высота стеков всех его методов. Это ограниченный анализ, не полноценный verifier AVM2. По умолчанию результат неномерной; ни он, ни frozen-кандидат не предназначены для установки как plain DEV SWF: SteamEntry/FPS-адаптация сюда не включена.

Manifest сохраняет хеши входов, собственных исходников, инструментов и выходов. После изменения исходника не использовать старый compiled module: сборщик проверяет соответствие. Номерной кандидат: обновить VERSION, зафиксировать чистый source, скомпилировать native module и добавить `--freeze` к build_field_preview; повторить сборку в новом каталоге и сверить байты. Freeze записывает exact commit/version и отвергает незаписанные изменения. DEV-адаптация/установка выполняются отдельно.

## Проверки без игры

`python -m unittest discover -s tests` проверяет Python-инструменты и синтетические границы. Это не симулятор боя.

Режим `contract-tests` создаёт самостоятельный SWF с собственными Frame/Session/Layer, NeedleObservationMatch и тестовым root, без game ABC/изображений. `tests/air/PreviewContractTests.as` проверяет Frame/Session/Layer в настоящем AIR; native provider/controller не входит в этот harness и не считается проверенным его результатом.

Для локального запуска использован отдельный captive AIR29.0.0.113 контейнер с generic `CaptiveAppEntry.exe`, собственным application.xml из `tests/air/`, приватной копией AIR runtime и отдельным appID. Профиль `extendedDesktop` позволил войти в конструктор; при `desktop` в испытанном контейнере процесс оставался без выполнения теста. Это наблюдение конкретной конфигурации, не правило для любых AIR-пакетов. Runtime и упаковочные файлы остаются только в ignored local. Не использовать игровой exe/root-класс как тестовый runner.

Runner пишет `results.json` только в собственный `File.applicationStorageDirectory` и завершает процесс с кодом 0/1. Проверять exit code **и свежесть** файла относительно запуска; прежний passed-файл не является новым результатом. Игра, её appID, сохранения и запускатель здесь не используются.

## Что остаётся настоящей игровой проверкой

Загрузка нового ABC и нативных привязок, выбор hover/selected цели, очистка при отмене/commit/смене боя, движение камеры/HUD, положение меток и длительность native provider требуют DEV. Служебный текст `ARM / STR / SW` и смещение — измерительный инструмент, не принятый дизайн. `SW` здесь конечное число известных бонусов при изменении ауры, не окончательная пользовательская нотация. Нет автоматической раскладки при перекрытиях.

До установки сформировать отдельный обратимый кандидат, сохранить проверенные DEV-адаптации и закрыть целевую игру. Не выдавать компиляцию или успешный автономный harness за runtime/UX-приёмку мода.

## Исследовательский режим Needle

`--mode native-banner-ui` добавляет к выбранной баннерной подаче «Таран», сохраняя прежние режимы. Расчёт Ram и observer/calculation Needle переиспользуются, native hooks те же три у полевого модуля. В общий renderer поступает прежний Ram Frame с фильтрацией соседей; отдельный технический слой для него не выводится. Знаки дельт after−before включают `+`, отрицательные значения и0. Изменение ауры обозначается отдельно локализованным именем Shield Wall с дельтой количества бонусов, без повторного прибавления к броне. Суффикс кандидата FieldPreview-BannerUI; отображение Ram/ауры требует новой пользовательской приёмки, прежняя Needle test.16 не расширяет её автоматически.

`--mode native-needle-ui` — отдельная следующая проба выбранного UI. Переиспользует расчёт/наблюдатель test.15; результат адаптируется в Frame с явным allTargets, чтобы защищённые промежуточные цели не отсеивались. Неиспользуемые здесь поля ауры нейтральны, эта проба не заявляет прогноз ауры Needle. Дельты — дочерние объекты настоящего flag.movieClip, центры взяты из arm_text/str_text.textField, шрифт штатный с увеличением на2 и тёмной обводкой без фона. Координаты и scale самого баннера не меняются. При смене класса флага берётся текущий экземпляр публичного flags.

Для этого режима сборщик дополнительно меняет только operand чтения battleInfoFlagVisible в ScenePageBattleInfoFlags._updateEntity: NeedleBannerPreview.requested(entity,nativeRequest). Проверки enabled/visibleToPlayer/active/stats и нативные setEntityAndStats/add/remove/update остаются прежними. Политика действует только для board с ready Needle Frame; после clear возвращается исходный запрос. Переоценка флагов вызывается штатным BATTLE_INFO_FLAG_VISIBLE, модельный Boolean не перезаписывается. Всего три hooks: прежние ScenePage update/cleanup и новый visibility operand. Состав проверяется побайтовым сравнением тегов/методов и стеков; runtime/UX подтверждает пользователь. Суффикс кандидата FieldPreview-NeedleUI.

`--mode native-needle-probe` вместо `native-module` добавляет собственный `NeedlePreviewProbe` и генерирует вариант controller. Обычный режим и исходные Frame/Session/Layer/FieldPreview не меняются. Сборщик выбирает суффикс `FieldPreview-NeedleProbe`; нужен новый номер при передаче в DEV, а не пересборка test.10.

Проба запускается только после штатного выбора линии Needle, читает упорядоченный targetSet и пишет `BSUI_NEEDLE_QUERY`. Она не добавляет чисел/hover-поведения на экран. В detached fake Stats вызывает native DAMAGE_STR/CHANGE_STAT в порядке execute-all/apply-all, затем проверяет восстановление Stats/modifiers, RNG, позиций, effects и действия. Неизученные состояния, летальный результат, таланты и отличающиеся fake/live защитные пути дают явный unsupported; ошибка восстановления отключает дальнейшие запросы текущего board через PreviewSession.

Для ready-прогноза controller ждёт native manager EXECUTING, исключает fake и сопоставляет описание запроса/исходное состояние через чистый NeedleObservationMatch. Затем ABILITY_AND_CHILDREN_COMPLETE принимается по identity именно привязанного реального действия (путь test.15). До callback смены хода он читает реальные ARM/STR и resistance tags native effects, пишет независимый `BSUI_NEEDLE_ACTUAL MATCH/MISMATCH`. ARM/BIND/REJECT/EVENT/SKIP/PENDING и ошибки подготовки явно логируются; callback вызывает отдельный read-only collector. Слушатель снимается после результата, при следующем запросе и dispose; максимум одна ожидающая пара. Это диагностическая сверка ограниченного прямого действия, не вычисление каскадов и не готовый production provider. Временный fail-closed guard зарядов использует exact-build getDebugStringMods; не переносить его как универсальный парсер механики.
