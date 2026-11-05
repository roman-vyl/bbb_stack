# Deploy и поздняя авторизация ABI

Совместимые ABI и Runtime закреплены точными SHA в deploy/images.env. ABI включает #55, Runtime — #47 вместе с #46. Эти версии применяются совместно с данной Compose-конфигурацией; заменять только один компонент на прежнюю версию нельзя. Сам Deploy на действующий Demo и реальный Bybit smoke требуют отдельного разрешения. Точный состав выпуска и точки проверки — в [release review](releases/abi-runtime-authorization-v1.md). Обычный workflow Deploy Demo сохранён.

В окружении runner задайте ABI_EXPECTED_BYBIT_UID — доверенный UID именно Demo-аккаунта (не родительского mainnet). Это несекретная настройка, не значение из передаваемого кандидата. Уберите API credentials из ABI env_file; Compose больше его не подключает. Торговые настройки, risk sizing, hedge и существующие данные остаются.

Перед переключением оператор сверяет прочие настройки старого bybit-demo.env и явно переносит необходимые несекретные overrides в Compose. Агент файл с ключами не читает. Обычный Deploy обновляет весь стек без пароля: ABI жив в LOCKED, Runtime запускается по liveness. AUTHORIZED и Trading READY проверяются отдельно через /health/ready; /health/live не разрешает торговлю.

Лимит ABI по умолчанию 1 GiB, memory и memswap равны; он настраивается ABI_MEMORY_LIMIT. При подготовке измерено около 60 MiB потребления работающего ABI, без изменения текущего контейнера; выбран запас, а не ограничение впритык. Внутри нового контейнера необходимо подтвердить memory.swap.max=0, tmpfs и владельца каталога uid 1000/mode 0700. Секреты не монтируются в контейнер и не передаются Docker environment.

После отдельного разрешения на Demo-переключение:

```sh
python3 scripts/authorize_abi.py status
python3 scripts/authorize_abi.py authorize /path/to/credentials.age
python3 scripts/authorize_abi.py retry
```

Команда сама находит один работающий сервис abi по Docker labels основного Compose-проекта bbb_stack. Поиск не читает Compose/env-файлы и не требует runner variables; для другого имени проекта есть --project (или COMPOSE_PROJECT_NAME). Нужен соседний ABI checkout с scripts/abi-authorize.py (или --abi-repo). Она не делает compose up, restart, pull, перенос данных или создание контейнера. age запрашивает пароль на Mac. Проверка ключей даёт AUTHORIZED, проверка существующих торговых привязок — Trading READY. При временной ошибке ABI сам повторяет авторизацию или недоступную проверку торговых привязок: задержки 5/15/30 секунд, затем по 30 секунд. Пароль не вводится повторно, Mac/Python не участвуют в повторных попытках. Ручной retry остаётся диагностическим. Replay/cleanup, observers и торговые POST таймер не повторяет; остановка ABI отменяет повторы. После рестарта снова LOCKED.

До READY контролируйте Runtime, чтобы не запустить несогласованный торговый цикл. При потерянном ответе сначала status. Никакой автоматической повторной передачи credentials. При откате сначала сверить реальные заявки/позиции, вернуть прежний проверенный image manifest и Compose-конфигурацию. Старый env-файл нужен только прежнему образу; в новой версии fallback нет. Mainnet запрещён.
