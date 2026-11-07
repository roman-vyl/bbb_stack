# Bybit Mainnet: подготовка и переключение

Реализация не выполняет cutover автоматически. Deploy, архивирование/подготовка данных,
авторизация и включение стратегий — отдельные действия владельца. Работающий Demo не менять
до согласованного окна. Mainnet использует тот же проект `bbb_stack`, DNS и loopback ports;
одновременно запускать Demo и Mainnet, а также их Deploy workflows, нельзя.

## Перед первым Deploy

1. Дождаться merge Mainnet ABI PR, успешных CI и Docker Publish. Отдельным PR установить
   `ABI_IMAGE` в `deploy/images.mainnet.env` на фактически опубликованный полный SHA этого
   ABI commit. Сейчас значение намеренно пустое: запуск и preflight остановятся. Остальные
   пять pins совпадают с Demo; `deploy/images.env` и Demo workflow не меняются.
2. Записать Demo root, project, фактические image refs и конфигурацию для отката. Подтвердить
   доверенный UID целевого Mainnet аккаунта независимо от создаваемого API key. Проверить,
   что аккаунт работает с уже поддержанными глобальными `api.bybit.com` и `stream.bybit.com`.
3. Согласовать drain Demo: остановить поступление новых торговых решений, завершить активные
   циклы и проверить orders/positions. Затем отдельно остановить стек. Этот документ не
   предлагает закрывать позиции удалением локальных файлов.
4. После остановки всех writers сделать согласованный архив следующих каталогов. Оригиналы
   Demo оставить на месте. SQLite сохранять вместе с имеющимися `-wal`, `-shm`, `-journal`;
   не копировать только основной файл во время записи.

| Demo root: сохранить/архивировать | Mainnet root: начать заново |
| --- | --- |
| `strategy-runtime/state/`, включая `runtime_state.jsonl` | Пустой `strategy-runtime/state/` |
| `strategy-runtime/journal/`, включая `runtime.jsonl` | Пустой `strategy-runtime/journal/` |
| `abi/`: correlation, diagnostics, facts DB и прочие var-файлы | Пустой `abi/`, кроме скопированного `config/`; facts создастся как `abi_exchange_facts_mainnet.sqlite3` |
| `journal/`, включая `journal.sqlite3` и ingest cursors | Пустой `journal/` |
| `strategy-runtime/specs/` | Отдельные копии JSON deployments, **каждый `enabled: false`** |

Сохранить без изменения торговых параметров `abi/config/abi.json`,
`strategy-runtime/config/runtime.toml`, `strategy-engine/engine.toml` и скопировать их в
аналогичные Mainnet directories. Отсутствующие optional config files не создавать из новых
значений по умолчанию. Согласовать `live_entry_mode` ABI/Engine/Runtime, сохранить
`order_lifetime_bars` и параметры raw_spec.

Историю **`market-data/`, `mds/markets.toml`, `research/` целиком** оставить на прежнем месте:
Mainnet монтирует её из Demo root. Не обнулять её, не копировать поверх и не запускать второй
writer. Research `/runtime-specs` при этом направляется только в Mainnet catalog.

5. Отдельно подготовить новый непересекающийся root и каталоги:
   `abi/config`, `strategy-engine`, `strategy-runtime/{config,specs,state,journal}`, `journal`.
   Требуются читаемые config/specs и writable durable directories существующих container
   users. Preflight не создаёт пути и не исправляет права. Не использовать symlinks внутри
   торговых деревьев. Проверить соответствие архива текущим файлам до дальнейших действий.

## Runner и Compose

На self-hosted runner нужны отдельные значения:

- `BBB_MAINNET_DATA_ROOT`: абсолютный отдельный Mainnet root;
- `BBB_DEMO_DATA_ROOT`: прежний root с сохранённой историей;
- `ABI_MAINNET_EXPECTED_BYBIT_UID`: доверенный Mainnet UID; Demo UID не используется;
- необязательный `ABI_MEMORY_LIMIT`, как в Demo.

Workflow загружает **только** `deploy/images.mainnet.env`, устанавливает `BBB_DATA_ROOT` в
canonical Mainnet root и использует `COMPOSE_PROJECT_NAME=bbb_stack`. Не подставлять API keys
в runner environment и не загружать Demo manifest поверх Mainnet pins.

Правильный порядок файлов: `docker-compose.yml`, `docker-compose.deploy.yml`,
`docker-compose.mainnet.yml`. Mainnet идёт последним, иначе deploy override заменит MDS
mounts обратно на Mainnet root. Для ручного read-only render нужны те же переменные и pins.

Ручной workflow **Deploy Mainnet** запускается только после отдельного разрешения.
На первом запуске оставить `first_launch=true`. Preflight проверяет paths, history,
отсутствие работающего Demo/другого контейнера с теми же данными, свежую память и disabled
catalog. Дополнительно pinned Runtime image проверяет catalog своим существующим loader
в одноразовом контейнере без сети с read-only mounts. Это не запуск второго Runtime service.

Deploy принудительно пересоздаёт существующий стек без build/volume removal, проверяет шесть
image refs, health, Mainnet environment и ABI LOCKED. Порядок сохраняется: ABI/Engine →
Runtime → MDS; Research ждёт Engine/MDS, Journal независим. ABI healthcheck — `/health/live`;
его trading readiness до авторизации возвращает 503 и не требует пароля для Deploy.

Повторный разрешённый Deploy: `first_launch=false`. Собственная память Mainnet и enabled
настройки сохраняются, ABI снова LOCKED. Workflow не архивирует, не сбрасывает state и не
выключает/включает стратегии. После неудачного первого запуска не переключать флаг ради
обхода проверки: изучить созданную память и согласовать дальнейшие действия отдельно.

## Авторизация и допуск

Владелец отдельно создаёт ключи Mainnet и шифрует JSON `[apiKey, apiSecret]` существующим
age-механизмом. Не монтировать `.age` в сервис, не писать plaintext/env-файл. Для выбранного
аккаунта linear verifier требует trusted UID, `readOnly=0` и `ContractTrade: Order, Position`.

После успешного Deploy отдельным разрешённым действием используется существующий клиент:

```sh
python3 scripts/authorize_abi.py status --project bbb_stack
python3 scripts/authorize_abi.py authorize /absolute/path/to/mainnet.age --project bbb_stack
```

Нужен ABI checkout с reviewed `scripts/abi-authorize.py` (опция `--abi-repo`). Клиент находит
уже работающий контейнер, не делает Deploy/restart, проверяет tmpfs/swap и доставляет
credentials через stdin/socket. Пароль спрашивает age. При потере ответа сначала `status`;
временные ошибки ABI повторяет самостоятельно. После рестарта/Deploy снова LOCKED.

`AUTHORIZED` не заменяет trading readiness. До включения любой стратегии отдельно проверить
read-only средствами аккаунта/существующих API:

- целевой UID и UNIFIED/linear USDT; согласованные orders/positions, без чужой экспозиции;
- **cross = `REGULAR_MARGIN`**, это свойство Bybit account, не Compose env. Код sizing также
  поддерживает portfolio, но для этого cutover выбран cross; isolated не подходит;
- hedge slots `positionIdx=1/2` для каждого будущего инструмента с учётом symbol overrides.
  Пустой local replay и READY не доказывают, что все будущие символы в hedge;
- баланс и каждый `risk_multiplier`: `1` означает 1% всего `totalWalletBalance`, количество
  округляется вниз; комиссия и проскальзывание в этой формуле не учтены;
- Runtime `/v1/strategy-instances`: нет invalid/duplicate/skipped deployments, все disabled.

Автоматических switch-position-mode/set-margin-mode, торгового smoke или изменения leverage
нет. Если режимы не подходят, остановить допуск; настройку аккаунта владелец согласует отдельно.
После авторизации стратегии остаются выключенными до отдельного решения владельца и
существующего enabled-control API. Не включать стратегии ради проверки подключения.

## Откат

Остановить Mainnet отдельно, сохранить его память и проверить его реальные orders/positions.
Возврат Demo pins/config/root не закрывает Mainnet позиции. Возобновление Demo требует
отдельного решения, его прежних данных и собственной авторизации. Не переносить Mainnet
correlation/state/Journal в Demo и не восстанавливать Demo архив поверх Mainnet root.
