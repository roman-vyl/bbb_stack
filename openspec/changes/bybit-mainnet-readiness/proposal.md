## Why

BBB уже поддерживает Mainnet endpoints, но ABI запрещает Mainnet в verifier и live guard. Нужен минимальный, проверяемый переход с Demo с отдельной торговой памятью и сохранением поздней age/socket-авторизации.

## What Changes

- В ABI разрешить Mainnet в существующем verifier и live guard, сохранив UID, права, dry-run, readiness и все торговые проверки.
- В Stack добавить отдельный Mainnet Compose override и ручной Mainnet Deploy по образцу Demo; действующие Demo override, workflow и `deploy/images.env` не менять. Для Mainnet использовать отдельный immutable manifest.
- Описать подготовку отдельного data root, архивирование торговых файлов, сохранение MDS/Research и первый старт с `enabled: false` у всех стратегий.
- Исправить только затронутые устаревшие инструкции о plaintext env-ключах и запрете Mainnet.

## Capabilities

### New Capabilities

Нет.

### Modified Capabilities

- `bbb-live-stack`: добавить требования к безопасному Mainnet-переключению существующего стека. ABI остаётся владельцем своего контракта; этот OpenSpec задаёт системные критерии приёмки и минимальный объём связанной правки ABI.

## Impact

Будущая реализация: `roman-vyl/abi_executor_bot` — verifier, composition-root type, live guard, тесты и документация; `roman-vyl/bbb_stack` — Mainnet override/workflow/manifest, проверки и runbook. Runtime, Engine, MDS, Journal, Research: изменения кода не требуются. Торговая логика, sizing, контракты HTTP и архитектура сохраняются.

Текущий PR содержит только аудит и OpenSpec. Apply, подготовка/копирование данных, ключи, Deploy и реальная авторизация требуют последующего разрешения пользователя и сейчас не выполняются.
