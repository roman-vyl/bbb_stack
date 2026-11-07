## 1. ABI — после разрешения Apply

- [x] 1.1 В отдельном ABI PR расширить verifier policy/allowlist и фиксированную host map для mainnet; убрать сужающий cast в server и только Mainnet-запрет в live guard. Обновить затронутые ABI docs без изменения торговой логики.
- [x] 1.2 Добавить fake-only проверки всех трёх hosts, UID/rights rejection, temporary failure и Mainnet live guard с/без authorization, dry-run и live-enabled. Проверить LOCKED → AUTHORIZED без restart и restart → LOCKED существующим dummy transport; никаких реальных Bybit writes. Запустить ABI `npm test`, `npm run typecheck`, `npm run build`.

## 2. Stack — после разрешения Apply

- [x] 2.1 Добавить Mainnet override с прежними risk/hedge/live/facts и защитой socket; отдельные trading mounts, повторное использование существующих MDS/Research history, Mainnet Research export catalog. Сохранить Demo файлы без изменений.
- [x] 2.2 Добавить ручной Mainnet workflow и отдельный manifest с пятью прежними SHA pins и заблокированным ABI pin до публикации образа. Проверять Mainnet UID, canonical isolation paths, наличие истории и отсутствие работающего Demo до mutation; сохранить pull/config/health/image checks и cleanup GHCR, принудительно пересоздавать ABI, проверять LOCKED. Не авторизовать и не менять strategy enabled.
- [x] 2.3 Проверить Compose render и workflow статически на dummy paths/UID: pins, effective env, все mounts, ordering, loopback, tmpfs/no-swap/core, отсутствие ключей; отрицательные случаи missing paths/UID, aliasing и работающий Demo. Выполнить имеющиеся stack checks; тест повторного Deploy/LOCKED делать только изолированно с dummy credentials, без рабочего стека.

- [ ] 2.4 После merge ABI PR #58 и успешного Docker Publish отдельным PR заполнить `ABI_IMAGE` фактически опубликованным SHA. До этого Mainnet manifest намеренно не запускается. Merge и публикация образа не выполнялись в рамках Apply.

## 3. Runbook и ревью — без выполнения cutover

- [x] 3.1 Описать архив/новую память по таблице design, сохранение MDS/Research, disabled catalog до первого старта, отдельные authorization/account preflight и безопасный rollback. Обновить устаревшие затронутые инструкции env_file; не изменять стратегии/данные.
- [x] 3.2 Проверить first-start сценарий с пустой памятью и disabled fixtures, согласованность source/cursors Journal и сохранение собственной памяти при redeploy; подтвердить отсутствие изменений Runtime/Engine/MDS/Journal/Research кода.
- [x] 3.3 Опубликовать implementation PRs и результаты проверок, остановиться перед любым реальным Deploy, архивированием/подготовкой данных, авторизацией или включением стратегий. Эти операции не входят в Apply без отдельного разрешения владельца.

## Результат Apply

ABI PR: https://github.com/roman-vyl/abi_executor_bot/pull/58. ABI: 1152 теста, typecheck/build/OpenAPI прошли. Stack: 12 тестов, YAML/bash syntax и strict OpenSpec validation прошли. Реальный Docker Deploy/recreate и pinned-image catalog smoke не запускались; fresh/redeploy guards проверены fixtures и mocks, авторизация/replacement LOCKED — реальным composition root с fake transport. Тесты, требующие localhost/Unix sockets, выполнены вне ограничивающего их sandbox, без реальных ключей/Bybit/рабочего стека. Остался только release-dependent ABI image pin; cutover не выполнялся.
