## Context

Аудит 2026-11-07: исходники, Compose, workflow и закреплённые версии; работающие контейнеры, runner environment, ключи и каталоги данных не инспектировались. Состояние реального аккаунта не подтверждено. Мотивация — в `proposal.md`.

Проверенные ревизии: Stack `333072891d3e402725bf6e676b551101e2ae0da7`, ABI `c21ca11d9795099a4a1d2d3e261da181c98cbb75`; обе совпадают с GitHub main на момент аудита. Остальные deployment pins — `deploy/images.env`. Локальные Runtime/MDS/Journal/Research checkout отличаются от pins; config Runtime и Journal проверен через GitHub именно по pins, MDS settings — по закреплённому git object. Это аудит реализации, не аттестация фактически запущенных образов.

| Область | Факт и необходимая правка |
| --- | --- |
| ABI config/REST/private WS | `src/config/config.ts` уже принимает mainnet; `src/exchange/bybitAdapter.ts` выбирает `https://api.bybit.com`; `src/exchangeStream/exchangeStreamRecorder.ts` содержит `wss://stream.bybit.com/v5/private`. Менять endpoints этих компонентов не нужно. |
| Verifier | `src/authorization/bybitCredentialsVerifier.ts`: union и runtime allowlist только demo/testnet; ternary host отправляет любой не-demo в testnet. Добавить mainnet и явную фиксированную таблицу трёх hosts; сохранить HMAC/GET, UID, `readOnly=0`, linear `ContractTrade: Order, Position`, дедлайн 10 s, 64 KiB, запрет redirect и существующие отказы/retry. |
| Composition root | `src/app/server.ts` приводит environment к demo/testnet. Убрать сужение типа после расширения policy; не менять lifecycle. |
| Live guard | `src/execution/liveGuard.ts` независимо блокирует mainnet. Удалить только этот запрет; сохранить остальные gates и admission readiness. Verifier без этой правки недостаточен. |
| Authorization | `AuthorizationService` всегда начинает LOCKED. `scripts/abi-authorize.py` уже принимает произвольный `.age` с JSON-парой и доставляет через stdin/socket; смена клиента не нужна. Stack `scripts/authorize_abi.py` находит существующий ABI по Compose labels, принимает `--project`; ничего не запускает. |
| risk / cross | `RiskPercentPositionSizeCalculator`: `totalWalletBalance × risk_multiplier / 100 / abs(entry-stop)`, округление вниз, без учёта комиссии/проскальзывания; `1` означает 1%. Поддержаны `REGULAR_MARGIN` и `PORTFOLIO_MARGIN`, isolated отклоняется. Для этой миграции целевой режим — cross/REGULAR_MARGIN; алгоритм и текущую поддержку portfolio не менять. Нового env `cross` нет. |
| hedge | Demo уже задаёт hedge. `bybitPositionModeAssurance.ts` проверяет факты positionIdx, не переключает биржу. Startup проверяет только активные replay bindings; на пустой памяти это не доказательство hedge всех символов. Перед admission есть существующая проверка конкретного binding. |
| Runtime / Engine | Exchange environment не выбирают: используют внутренние URL. Сохранить entry mode, `order_lifetime_bars` и параметры стратегий; новые env/код не нужны. Runtime хранит journal/state и выбирает только enabled deployments. |
| MDS | `runtime/settings.py`: публичные Mainnet REST и WS уже defaults, база `/data/market.sqlite3`. Сохранить историю и `mds/markets.toml`; код/источник не менять. |
| Journal | Pin config использует только Runtime source, собственный SQLite и ABI URL. Источник и база должны смениться вместе; код и внутренний URL остаются. SQLite содержит также ingest progress — Demo БД не переносить. |
| Research | Сохранить `/data` целиком (runs/configs и прочие существующие артефакты), но `/runtime-specs` направить в новый Mainnet catalog. |

Источники Bybit: [hosts/auth](https://bybit-exchange.github.io/docs/v5/guide), [API key information](https://bybit-exchange.github.io/docs/v5/user/apikey-info), [account marginMode](https://bybit-exchange.github.io/docs/v5/account/account-info), [position modes](https://bybit-exchange.github.io/docs/v5/position/position-mode). Региональный host целевого аккаунта необходимо подтвердить до cutover: план использует уже имеющийся глобальный Mainnet host; несовместимый региональный аккаунт — причина остановить переход, а не добавить произвольный host override.

## Goals / Non-Goals

**Goals:** разрешить существующий execution path для Mainnet и сделать явными границы окружений и безопасный первый старт.

**Non-Goals:** новые сервисы, secret storage, переключатель режимов биржи, изменение sizing/торговых решений, автоматический перенос открытых сделок, одновременный Demo/Mainnet на текущих host ports. Сейчас создаются только planning artifacts.

## Decisions

1. **Отдельные файлы Mainnet.** Добавить `docker-compose.mainnet.yml`, `deploy/images.mainnet.env`, `.github/workflows/deploy-mainnet.yml`; использовать порядок base + deploy + mainnet, без demo override. Mainnet должен идти последним: `docker-compose.deploy.yml` уже заменяет MDS volumes через `!override` и иначе вернёт их на неверный root. Это сохраняет рабочий Demo и его manifest. Параметризация существующего Demo workflow затронула бы рабочий путь и расширила scope. Mainnet manifest содержит все шесть точных SHA refs: первоначально прежние пять, ABI — новый опубликованный SHA после отдельного ABI PR/CI. Не использовать main/latest и не загружать оба manifest в GITHUB_ENV: shell env перекрывает `--env-file`.

2. **Изоляция существующими bind mounts.** Mainnet override требует `BBB_MAINNET_DATA_ROOT` и `BBB_DEMO_DATA_ROOT` для проверки границ; workflow устанавливает `BBB_DATA_ROOT` равным Mainnet root. Все торговые каталоги берутся оттуда. В override явно заменить полные volume lists MDS и Research через уже используемый `!override`: MDS config/data берутся из прежнего `${BBB_DEMO_DATA_ROOT}/mds` и `/market-data`; Research `/data` — из прежнего `/research`, `/runtime-specs` — из Mainnet root. Это сохраняет данные без копирования больших SQLite и изменения приложения. Проверять canonical paths всех торговых директорий на пересечение с Demo, включая symlinks; mounts Research catalog, Runtime source и ABI var должны согласовываться. Для существующей истории проверять наличие директорий/файлов до `up`, запретить автоматическое создание отсутствующих source directories в новых mounts.

3. **Один стек в момент времени.** Сохранить существующий Compose project `bbb_stack`, DNS и ports. Будущий cutover останавливает Demo после согласованного drain, перед запуском Mainnet; параллельные Deploy Demo/Mainnet и два writer MDS/Research запрещены операционным порядком. Это не новый параллельный стек. Никакого stop во время текущего аудита. Mainnet workflow до `up` проверяет, что старые контейнеры этого проекта остановлены либо относятся к тому же Mainnet root/environment; работающий Demo не заменяет автоматически. В документации явно запретить одновременный запуск двух workflow; Mainnet jobs сериализовать, не отменяя выполняющийся deploy.

4. **Deploy без авторизации.** Сохранить GHCR login/cleanup, pull, Compose validation, `--no-build`, отсутствие volume removal, health polling с ошибкой по timeout и проверку всех шести running image refs. Для Mainnet использовать `up -d --no-build --remove-orphans --force-recreate`: текущий `up` без force может оставить AUTHORIZED контейнер при неизменной конфигурации. Сохранить ABI tmpfs 0700 uid/gid 1000, core=0, memory=memswap; не монтировать `.age`, не читать ключи в workflow. После Deploy проверить Mainnet env, `authorization=LOCKED`, `canExecuteLive=false`, ABI `/health/live`, Runtime live/ready. ABI `/health/ready=503` до авторизации ожидаем и не блокирует запуск Runtime: Compose проверяет ABI liveness. Авторизация отдельной существующей командой через найденный ABI, без restart.

## Migration Plan

Только будущая инструкция после разрешения; сейчас ни один шаг не выполняется.

1. Выпустить и проверить ABI-правку отдельно; подготовить Mainnet override/workflow/manifest и runbook без запуска. Записать прежние image pins и конфигурацию для rollback. Mainnet UID берётся из доверенного источника отдельно от предъявленного ключа; не наследовать Demo UID runner автоматически: использовать отдельную переменную Mainnet UID и передавать её как `ABI_EXPECTED_BYBIT_UID`.
2. Согласовать остановку торговли Demo и проверить открытые orders/positions; локальный reset не отменяет биржевую экспозицию. После завершения активных циклов остановить единственный стек. Сделать согласованный архив перечисленных каталогов: файлы SQLite вместе с имеющимися `-wal`, `-shm`, `-journal`, после остановки writers. Не копировать только основной SQLite во время записи.

| Путь относительно прежнего data root | Архив / Mainnet |
| --- | --- |
| `strategy-runtime/state/` (`runtime_state.jsonl`) | Архивировать целиком, Mainnet начать пустым: исключить replay старых циклов/management state. |
| `strategy-runtime/journal/` (`runtime.jsonl`) | Архивировать целиком; новый журнал. Journal source указывает на него. |
| `strategy-runtime/specs/` | Сохранить оригинал и архив; копировать только deployment definitions в отдельный Mainnet catalog с каждым `enabled: false`. Не редактировать оригинал. |
| `abi/` без секретов | Архивировать весь var, включая `abi_entry_package_correlation.jsonl`, `abi_diagnostics.jsonl`, `abi_exchange_facts_demo.sqlite3` и SQLite sidecars; неизвестные/legacy var-файлы тоже сохранить. В Mainnet не переносить торговые файлы; facts создаётся как `abi_exchange_facts_mainnet.sqlite3`. Одного нового имени facts недостаточно: correlation не имеет environment namespace. |
| `abi/config/abi.json` | Сохранить и скопировать конфигурацию, не торговое состояние. |
| `journal/` (`journal.sqlite3` и sidecars) | Архивировать целиком; новая БД и ingest cursors. Не направлять старую БД на новый Runtime source. |
| `strategy-runtime/config/runtime.toml`, `strategy-engine/engine.toml` | Сохранить и скопировать в Mainnet root без изменения торговых параметров; отсутствующие optional files не выдумывать. |
| `market-data/`, `mds/`, `research/` | Сохранить на месте полностью и повторно смонтировать; не очищать, не пересоздавать, не переносить в trading archive. |

3. Подготовить Mainnet dirs и отключённый catalog. До первого `up` проверить весь catalog валидным загрузчиком/контрактом: отсутствие enabled, невалидных или непрочитанных deployment-файлов; проверить пустоту новой trading memory и права mounts. Подготовка/архив — одноразовая ручная операция; повторный Deploy ничего не обнуляет и не отключает автоматически.
4. Выполнить отдельно разрешённый Mainnet Deploy; подтвердить image refs, mounts, startup order, LOCKED и отсутствие включённых стратегий по Runtime catalog API. При сбое оставить ABI LOCKED, не авторизовать.
5. Владелец отдельно создаёт и шифрует Mainnet keys существующим age-механизмом. Авторизовать без рестарта; сверить UID, AUTHORIZED и trading readiness. Read-only проверить UNIFIED, REGULAR_MARGIN, hedge slots каждого будущего linear USDT символа, balance и отсутствие несогласованных orders/positions. Никаких switch-position-mode, set-margin-mode или тестовых сделок. Если требуется настройка аккаунта, её выполняет владелец отдельно; до подтверждения стратегии выключены. Проверить каждый `risk_multiplier`; bankroll — весь `totalWalletBalance`, не отдельный бюджет стратегии.
6. Стратегии остаются выключены и после авторизации. Включение — отдельное решение владельца существующим enabled-control API.

Rollback: остановить Mainnet, сохранив его собственные данные; проверить/согласовать его биржевые orders/positions отдельно. Возврат прежних Demo pins/config/data root не закрывает Mainnet позиции. Возобновить Demo только отдельным разрешённым действием с его собственной памятью и авторизацией; не подсовывать Mainnet state старому ABI и не восстанавливать Demo поверх Mainnet root.

## Risks / Trade-offs

- Старые README и stack spec описывают plaintext env_file, хотя текущий Demo override его уже не использует → в реализации обновить затронутые инструкции; не брать устаревший текст за описание текущего кода.
- Общий project/ports сохраняет простоту, требует окна переключения и дисциплины единственного Deploy → не обещать zero downtime или параллельную работу; preflight отказывает при работающем Demo.
- Пустая локальная память не доказывает пустой аккаунт, hedge и cross → обязательный read-only preflight до enabled; readiness не заменяет эту проверку.
- Изменение только имени facts БД оставляет Runtime/ABI replay и Journal cursors от Demo → отделить все торговые mounts; MDS/Research оставить прежними с одним writer.
- Фактические host paths, конфигурация и UID не читались → перед cutover сверить их с этим планом; неизвестные значения сейчас не подставлять.
