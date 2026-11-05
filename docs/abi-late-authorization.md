# Deploy и поздняя авторизация ABI

Этот draft требует согласованного ABI integration image и Runtime с обработкой 503 execution_not_ready (Runtime PR #46). Текущие image pins не изменены: до согласованного выпуска образов и их закрепления эта конфигурация не должна применяться к действующему Demo. PR #103 с интерактивным deploy больше не нужен; workflow Deploy Demo сохраняется.

В окружении runner задайте ABI_EXPECTED_BYBIT_UID — доверенный UID именно Demo-аккаунта (не родительского mainnet). Это несекретная настройка, не значение из передаваемого кандидата. Уберите API credentials из ABI env_file; Compose больше его не подключает. Торговые настройки, risk sizing, hedge и существующие данные остаются.

Перед переключением оператор сверяет прочие настройки старого bybit-demo.env и явно переносит необходимые несекретные overrides в Compose. Агент файл с ключами не читает. Обычный Deploy обновляет весь стек без пароля: ABI жив в LOCKED, Runtime запускается по liveness. AUTHORIZED и Trading READY проверяются отдельно через /health/ready; /health/live не разрешает торговлю.

Лимит ABI по умолчанию 1 GiB, memory и memswap равны; он настраивается ABI_MEMORY_LIMIT. При подготовке измерено около 60 MiB потребления работающего ABI, без изменения текущего контейнера; выбран запас, а не ограничение впритык. Внутри нового контейнера необходимо подтвердить memory.swap.max=0, tmpfs и владельца каталога uid 1000/mode 0700. Секреты не монтируются в контейнер и не передаются Docker environment.

После отдельного разрешения на Demo-переключение:

```sh
python3 scripts/authorize_abi.py status
python3 scripts/authorize_abi.py authorize /path/to/credentials.age
python3 scripts/authorize_abi.py retry
```

Команда сама находит один существующий сервис abi в основном Compose-проекте. Нужен соседний ABI checkout с scripts/abi-authorize.py (или --abi-repo). Она не делает compose up, restart, pull, перенос данных или создание контейнера. age запрашивает пароль на Mac. Проверка ключей даёт AUTHORIZED, проверка существующих торговых привязок — Trading READY. Временная ошибка не требует нового пароля; retry не повторяет локальное восстановление. После рестарта снова LOCKED.

До READY контролируйте Runtime, чтобы не запустить несогласованный торговый цикл. При потерянном ответе сначала status. Никакой автоматической повторной передачи credentials. При откате сначала сверить реальные заявки/позиции, вернуть прежний проверенный image manifest и Compose-конфигурацию. Старый env-файл нужен только прежнему образу; в новой версии fallback нет. Mainnet запрещён.
