## 1. ABI — после разрешения Apply

- [ ] 1.1 В отдельном ABI PR расширить verifier policy/allowlist и фиксированную host map для mainnet; убрать сужающий cast в server и только Mainnet-запрет в live guard. Обновить затронутые ABI docs без изменения торговой логики.
- [ ] 1.2 Добавить fake-only проверки всех трёх hosts, UID/rights rejection, temporary failure и Mainnet live guard с/без authorization, dry-run и live-enabled. Проверить LOCKED → AUTHORIZED без restart и restart → LOCKED существующим dummy transport; никаких реальных Bybit writes. Запустить ABI `npm test`, `npm run typecheck`, `npm run build`.

## 2. Stack — после разрешения Apply

- [ ] 2.1 Добавить Mainnet override с прежними risk/hedge/live/facts и защитой socket; отдельные trading mounts, повторное использование существующих MDS/Research history, Mainnet Research export catalog. Сохранить Demo файлы без изменений.
- [ ] 2.2 Добавить ручной Mainnet workflow и отдельный six-image SHA manifest после ABI CI. Проверять Mainnet UID, canonical isolation paths, наличие истории и отсутствие работающего Demo до mutation; сохранить pull/config/health/image checks и cleanup GHCR, принудительно пересоздавать ABI, проверять LOCKED. Не авторизовать и не менять strategy enabled.
- [ ] 2.3 Проверить Compose render и workflow статически на dummy paths/UID: pins, effective env, все mounts, ordering, loopback, tmpfs/no-swap/core, отсутствие ключей; отрицательные случаи missing paths/UID, aliasing и работающий Demo. Выполнить имеющиеся stack checks; тест повторного Deploy/LOCKED делать только изолированно с dummy credentials, без рабочего стека.

## 3. Runbook и ревью — без выполнения cutover

- [ ] 3.1 Описать архив/новую память по таблице design, сохранение MDS/Research, disabled catalog до первого старта, отдельные authorization/account preflight и безопасный rollback. Обновить устаревшие затронутые инструкции env_file; не изменять стратегии/данные.
- [ ] 3.2 Проверить first-start сценарий с пустой памятью и disabled fixtures, согласованность source/cursors Journal и сохранение собственной памяти при redeploy; подтвердить отсутствие изменений Runtime/Engine/MDS/Journal/Research кода.
- [ ] 3.3 Опубликовать implementation PRs и результаты проверок, остановиться перед любым реальным Deploy, архивированием/подготовкой данных, авторизацией или включением стратегий. Эти операции не входят в Apply без отдельного разрешения владельца.
