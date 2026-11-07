# Переключение единственного BBB-стека

Один Compose, один `deploy/images.env`, один workflow **Deploy BBB**. Меняются окружение,
доверенный UID и каталог торговой памяти. ABI #58 слит; после успешных CI и Docker Publish
его опубликованный SHA закреплён в **общем** manifest. Оба окружения используют эти же
шесть образов.

1. Согласовать завершение активных циклов и проверить реальные orders/positions. Остановить
   текущий стек **при смене окружения**. Deploy блокирует смену окружения работающего стека.
2. Сохранить согласованный архив торговых файлов после остановки writers. При первом переходе
   подготовить отдельные Mainnet directories; работающую Demo-память не перемещать и не очищать.
3. В существующем workflow выбрать `demo` или `mainnet`, выполнить отдельно разрешённый Deploy.
4. Новый/пересозданный ABI запускается LOCKED. Авторизовать выбранный аккаунт через существующий
   `scripts/authorize_abi.py` и age без рестарта. Сам Deploy credentials не получает.
5. Перед включением стратегий проверить аккаунт и риски. Стратегии включаются отдельно
   существующим enabled-control API.

## Конфигурация

На runner остаётся `BBB_DATA_ROOT`: прежний общий root для MDS, Research и конфигурации ABI,
Engine и Runtime. Для Demo используется прежний `ABI_EXPECTED_BYBIT_UID`, для Mainnet —
отдельный доверенный `ABI_MAINNET_EXPECTED_BYBIT_UID`.

Workflow устанавливает `BYBIT_ENV` и `ABI_EXPECTED_BYBIT_UID` выбранного аккаунта, а также
`BBB_TRADING_DATA_ROOT`: Demo — `BBB_DATA_ROOT`, Mainnet — `BBB_DATA_ROOT/mainnet`.
Compose использует этот путь для ABI var, Runtime specs/state/journal и Journal database.
Research экспортирует стратегии в выбранный Runtime catalog. История MDS/Research и
настройки режимов входа остаются прежними.

ABI сохраняет `risk`, `hedge`, UNIFIED/linear/USDT и exchange facts; Deploy явно задаёт
`ABI_DRY_RUN=false`, `ABI_LIVE_TRADING_ENABLED=true`. Вне Deploy Compose по умолчанию dry-run.
Startup ordering не меняется: ABI/Engine → Runtime → MDS; Research ждёт Engine/MDS,
Journal независим. Все host ports остаются loopback-only.

Для ручного render/start нужны те же `BYBIT_ENV`, UID, `BBB_DATA_ROOT` и
`BBB_TRADING_DATA_ROOT`; применяются `docker-compose.yml` и существующий image-only
`docker-compose.deploy.yml`. Отдельных файлов Demo/Mainnet Compose больше нет.

## Память первого Mainnet-запуска

Архивировать Demo trading directories целиком. SQLite сохранять с имеющимися `-wal`,
`-shm`, `-journal` после остановки writers. В `BBB_DATA_ROOT/mainnet` подготовить:

| Demo: сохранить в архиве и на месте | Mainnet |
| --- | --- |
| `abi/`: correlation JSONL, diagnostics, exchange facts SQLite и legacy var | Пустой `abi/`; Mainnet facts создаётся заново |
| `strategy-runtime/state/runtime_state.jsonl` | Пустой `strategy-runtime/state/`, без старого state |
| `strategy-runtime/journal/runtime.jsonl` | Пустой `strategy-runtime/journal/` |
| `strategy-runtime/specs/` | Копии deployment JSON, **все `enabled: false`**, остальные параметры прежние |
| `journal/journal.sqlite3` и ingest cursors | Пустой `journal/` |

`abi/config/abi.json`, `strategy-runtime/config/runtime.toml`, `strategy-engine/engine.toml`
читаются из прежнего общего root; не менять entry mode, order lifetime и стратегические
параметры ради переключения. `market-data/`, `mds/` и `research/` сохраняются полностью.
Не создавать второй стек или второй writer этих данных. Торговые directories двух окружений
не должны пересекаться или ссылаться друг на друга; это проверяет оператор при подготовке.
Первый Mainnet-запуск требует чистой торговой памяти и всех `enabled: false`.
Бэкап, создание каталогов и копирование отключённых specs — отдельные ручные операции.
Deploy не определяет первый запуск по содержимому state, не валидирует/изменяет catalog,
не архивирует и не очищает данные.

Обычный Deploy Demo → Demo или Mainnet → Mainnet не требует остановки стека:
`up -d --no-build --remove-orphans` обновляет только необходимые контейнеры. Durable state
и enabled/disabled сохраняются. Если ABI не пересоздан, авторизация сохраняется; если
создан заново — он LOCKED и нужна отдельная авторизация. Workflow не сбрасывает её.
При смене окружения проверяется конфигурация существующего ABI, в том числе остановленного,
если другие контейнеры проекта ещё работают: сначала должен быть остановлен весь стек.

## Авторизация и включение

Ключи каждого окружения владелец создаёт и шифрует отдельно существующим age-механизмом.
Файл `.age` содержит JSON `[apiKey, apiSecret]`; plaintext env-files и API keys в runner
не используются. После Deploy отдельным разрешённым действием:

```sh
python3 scripts/authorize_abi.py status --project bbb_stack
python3 scripts/authorize_abi.py authorize /absolute/path/to/selected-account.age --project bbb_stack
```

Клиент находит существующий ABI, проверяет tmpfs/swap и передаёт credentials через stdin/socket.
При потерянном ответе сначала status; restart не нужен. AUTHORIZED не заменяет readiness.
Перед включением проверить UID, UNIFIED, **cross/REGULAR_MARGIN**, hedge positionIdx 1/2
каждого будущего инструмента и согласованную биржевую экспозицию. Cross — настройка аккаунта,
не новый env. ABI режимы биржи не переключает. На пустом replay READY не доказывает hedge
всех символов. Проверить `risk_multiplier`: 1 означает 1% totalWalletBalance, без комиссии
и проскальзывания. После авторизации стратегии остаются выключенными до решения владельца.

Для возврата остановить стек, выбрать Demo и его собственную память/ключ. Mainnet данные
сохранить отдельно; возврат конфигурации не закрывает реальные Mainnet позиции.
