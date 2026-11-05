# Совместимый выпуск ABI / Runtime / Compose

Выпуск подготовлен для отдельной проверки итоговой конфигурации. Разрешение на Deploy действующего Demo и настоящий Bybit smoke НЕ предоставлено; Mainnet запрещён.

## Точные версии

| Компонент | Merge commit / SHA-тег GHCR | Исходный PR |
| --- | --- | --- |
| ABI | `c21ca11d9795099a4a1d2d3e261da181c98cbb75` | [ABI #55](https://github.com/roman-vyl/abi_executor_bot/pull/55) |
| Runtime | `b7357ec64fd965127dd4dcf01ce47cd8c9a1759a` | [Runtime #47](https://github.com/roman-vyl/strategy_runtime/pull/47), включает #46 |
| Compose / локальная команда | текущая версия этого репозитория | [bbb_stack #105](https://github.com/roman-vyl/bbb_stack/pull/105) |

Единственный источник image refs — deploy/images.env, без :main/:latest. MDS, Engine, Research и Journal не обновляются этим выпуском. PR #55 включает независимые компоненты #52/#53/#54 целиком; промежуточные неработоспособные версии отдельно в main не сливались.

ABI OCI digest: `sha256:5e8cbc411bb74cb33f69a4880316a9276ea23b8b2dcc707d27162750eb4b1b2e`

Runtime OCI digest: `sha256:48b02521e2b7a0a39f74b866abfc84f74c5b726f22e296c2a8798b39282abf4a`

## Что проверяется перед эксплуатационным переключением

- Один прежний сервис abi, адрес abi:8787, прежние mounts данных и торговые настройки risk/hedge. Второго ABI и миграции данных нет.
- BYBIT_ENV=demo, Mainnet guard сохранён. ABI_EXPECTED_BYBIT_UID должен быть доверенным UID именно целевого Demo-аккаунта, а не родительского mainnet. Его значение не берётся из проверяемого кандидата. Оператор задаёт его в окружении runner до разрешённого Deploy.
- ABI env_file с открытыми ключами удалён. Оператор отдельно сверяет необходимые НЕСЕКРЕТНЫЕ overrides прежнего файла и переносит их явно; файл с ключами не читался агентом.
- Каталог /run/abi-authorization — tmpfs, uid/gid 1000, mode 0700; socket mode 0600. Memory/memswap равны, default 1 GiB, core=0. Фактический memory.swap.max=0 проверяется внутри нового контейнера до передачи секретов. Исключение swap macOS не гарантируется.
- Docker health использует /health/live: LOCKED ABI не блокирует старт Runtime. /health/ready проверяется отдельно: AUTHORIZED, localRecoveryReady и bindingsVerified не подменяют друг друга.
- На Mac нужны age в PATH, Python 3 и обновлённый ABI checkout с scripts/abi-authorize.py. Если имя Compose-проекта отличается от bbb_stack, используйте --project или COMPOSE_PROJECT_NAME. Поиск контейнера не требует runner env/Compose manifest.
- После одного ввода пароля ABI самостоятельно повторяет только безопасные проверки через 5/15/30/30… секунд. Торговые POST, local replay/cleanup и создание observers не повторяются. Restart возвращает LOCKED.
- Перед READY необходимо контролировать существующий Runtime и сверить реальные заявки/позиции, чтобы не начать несогласованный торговый цикл. Это часть отдельно разрешаемого переключения, не данного выпуска.

## Проверки выпуска

ABI CI: [main CI](https://github.com/roman-vyl/abi_executor_bot/actions/runs/42088468125).

ABI publish: [Docker Publish](https://github.com/roman-vyl/abi_executor_bot/actions/runs/42088617358).

Runtime CI: [main CI](https://github.com/roman-vyl/strategy_runtime/actions/runs/42089049644).

Runtime publish: [Docker Publish](https://github.com/roman-vyl/strategy_runtime/actions/runs/42089294964).

Локально ранее проверены 1150 ABI tests, typecheck/build/OpenAPI, 330 контрактных тестов Runtime и Compose/operator tests. Изолированный Docker+age smoke использовал публичные dummy credentials и test-only Bybit transport: временный отказ после одного пароля → автономный retry → AUTHORIZED/READY в том же контейнере; restart → LOCKED. Это не настоящая проверка Bybit Demo.

Перед закреплением pins проверяются успешная публикация и наличие linux/amd64 и linux/arm64 у обоих SHA-тегов. Compose config проверяется с тестовыми несекретными значениями путей/UID; значения рабочего runner требуют отдельной итоговой проверки.

## Откат

Предыдущая согласованная пара: ABI `0d8a111754dbffcd3418097c8a740474be773542`, Runtime `c2c14abb3f69a300b774e164b7e57d1ae2a9e405`, плюс Compose до #105. Откат требует возврата всей согласованной конфигурации, включая прежний способ передачи credentials старому образу. Новая версия env-fallback не поддерживает. До любого отката сначала сверяются реальные заявки/позиции с Bybit. Автоматический rollback или Deploy в рамках подготовки выпуска не выполняются.
