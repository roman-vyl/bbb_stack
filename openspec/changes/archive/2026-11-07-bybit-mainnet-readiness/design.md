## Context

Аудит 2026-11-07: исходники, Compose, workflow и закреплённые версии; работающие контейнеры, runner environment, ключи и каталоги данных не инспектировались. Состояние реального аккаунта не подтверждено. Мотивация — в `proposal.md`. Решение пересмотрено по указанию владельца: один стек и параметризация существующего Deploy.

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

Один набор шести образов, один Compose и один Deploy. Без отдельного Mainnet workflow,
manifest, проверочных сервисов/скриптов или новой системы управления окружениями.

## Decisions

1. В `docker-compose.yml` перенести существующую ABI tmpfs/no-swap/core защиту и параметры
   risk/hedge/facts. Параметризовать `BYBIT_ENV`, UID, live flags и `BBB_TRADING_DATA_ROOT`.
   Вне Deploy сохраняется dry-run. Удалить `docker-compose.demo.yml`: конфигурация общая.
   Существующий `docker-compose.deploy.yml` остаётся только слоем закреплённых образов.
2. Один `deploy/images.env` для Demo/Mainnet. Никаких изменений SHA до опубликованного
   релиза ABI #58; после его merge/CI/Docker Publish обновить общий ABI pin отдельным PR.
3. В существующий `.github/workflows/deploy-demo.yml` добавить выбор `demo/mainnet`, назвать
   workflow Deploy BBB. Общий project — `bbb_stack`, последовательные Deploy без отмены
   выполняющегося задания. Обычный Deploy в том же окружении использует прежний
   `up -d --no-build --remove-orphans` без остановки и force-recreate. Если контейнеры
   работают, сравнить выбранное окружение с конфигурацией существующего ABI (включая
   остановленный ABI при других работающих контейнерах); только смена окружения требует
   предварительной ручной остановки. Сохранить pull, health, image-ref checks и cleanup.
   Созданный заново ABI начинает LOCKED; неизменённый сохраняет авторизацию. Workflow
   не управляет credentials и не требует LOCKED от неизменённого ABI.
4. `BBB_DATA_ROOT` остаётся общим root истории/конфигурации. Demo trading root — прежний
   `BBB_DATA_ROOT`, Mainnet — `BBB_DATA_ROOT/mainnet`. Это сохраняет Demo layout без
   переноса. ABI var, Runtime specs/state/journal и Journal DB используют выбранный root;
   Research экспортирует в выбранные specs. MDS/Research history и настройки ABI/Engine/
   Runtime остаются прежними. Раздельные directories подготавливает оператор; новых
   проверочных скриптов/миграций нет. Один стек означает одного writer общей истории.
5. UID Demo берётся из прежнего `ABI_EXPECTED_BYBIT_UID`, Mainnet — из
   `ABI_MAINNET_EXPECTED_BYBIT_UID`; в контейнер передаётся один selected UID. Ключи не
   входят в конфигурацию: прежняя age/socket-команда после Deploy, без restart.
6. Чистая память и disabled catalog первого Mainnet-запуска — ручная подготовка оператора,
   как и бэкап. Deploy не определяет первый запуск по state, не проверяет catalog и
   не меняет enabled/disabled. При возврате окружение получает собственную прежнюю память.

## Migration Plan

Только инструкция будущего отдельно разрешённого переключения:

1. Выпустить ABI #58 и закрепить его опубликованный SHA в общем manifest. Записать прежние
   pins/конфигурацию. Проверить экспозицию и согласовать завершение активных циклов.
2. Остановить стек. Согласованно архивировать `abi/`, `strategy-runtime/state/`,
   `strategy-runtime/journal/`, `strategy-runtime/specs/`, `journal/` прежнего root.
   SQLite сохранять с sidecars после остановки writers; оригиналы Demo оставить на месте.
3. В `BBB_DATA_ROOT/mainnet` подготовить пустые `abi/`, `strategy-runtime/state/`,
   `strategy-runtime/journal/`, `journal/`; deployment JSON скопировать в отдельные specs,
   установив каждый `enabled: false`, остальные параметры сохранить. Старый correlation,
   facts, Runtime state/journal и Journal cursors не переносить. Общие config и история
   MDS/Research не меняются; новый facts SQLite автоматически получит Mainnet environment.
4. Выбрать окружение в Deploy BBB и запустить те же шесть образов. Созданный заново ABI
   будет LOCKED; отдельно авторизовать его соответствующим `.age`. До включения стратегий read-only
   проверить trusted UID, UNIFIED/linear/USDT, cross `REGULAR_MARGIN`, hedge slots каждого
   будущего символа, баланс, orders/positions и risk_multiplier. READY с пустыми bindings
   не доказывает hedge всех будущих символов. Режимы аккаунта автоматически не менять.
5. Стратегии включать только отдельным решением существующим enabled-control API.

Rollback: остановить стек, сохранить Mainnet память и проверить биржевые orders/positions;
выбрать Demo и его собственные данные/ключ. Возврат конфигурации не закрывает Mainnet позиции.
Полная таблица файлов и команды — `docs/mainnet-cutover.md`.

## Risks / Trade-offs

- Один project/ports требует остановки при переключении; параллельных стеков нет.
- Работающие контейнеры/host data/account в рамках Apply не инспектируются и не меняются;
  реальные пути, UID и настройки аккаунта подтверждаются владельцем при переключении.
