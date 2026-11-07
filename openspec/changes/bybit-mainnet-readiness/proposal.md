## Why

Единственный BBB-стек должен переключаться между Demo и Mainnet конфигурацией. Отдельная инфраструктура Mainnet не нужна: код, шесть контейнеров, SHA manifest и age-авторизация общие.

## What Changes

- Сохранить ABI PR #58 без изменений: Mainnet verifier и снятие отдельного Mainnet live-запрета.
- Параметризовать существующий Compose: `BYBIT_ENV`, trusted UID, торговый root и live flags; убрать отдельные Demo/Mainnet overrides.
- Расширить существующий Deploy workflow выбором `demo/mainnet`, оставив один `deploy/images.env`.
- Сохранить три защиты: раздельная торговая память; ABI LOCKED после каждого Deploy; все стратегии выключены на первом Mainnet-запуске.
- Сохранить общие MDS/Research history и конфигурацию; описать остановку, архив и авторизацию без изменения торговой логики.

## Capabilities

### New Capabilities

Нет.

### Modified Capabilities

- `bbb-live-stack`: переключение окружения единственного стека существующим Deploy.

## Impact

Stack: существующие Compose/workflow, короткий runbook и проверки. ABI #58 остаётся отдельным PR. Runtime, Engine, MDS, Journal, Research и age-клиент не меняются. Реальный Deploy, ключи, данные и стратегии не затрагиваются.
