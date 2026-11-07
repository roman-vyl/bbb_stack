## 1. ABI

- [x] 1.1 Оставить ABI PR #58 без изменений: Mainnet verifier/live guard и прежние safety gates.

## 2. Единый Stack Deploy

- [x] 2.1 Параметризовать общий Compose; перенести ABI auth-защиту, убрать environment-specific overrides.
- [x] 2.2 Расширить существующий Deploy выбором demo/mainnet и одним общим manifest; удалить отдельную Mainnet инфраструктуру из #109.
- [x] 2.3 Сохранить изоляцию памяти, LOCKED после Deploy и disabled первый Mainnet catalog; не менять данные/стратегии автоматически.
- [x] 2.4 Проверить оба Compose render, общие images/history/order, отказы при смешении памяти и enabled первом запуске; выполнить existing tests и YAML/bash validation.
- [ ] 2.5 После merge ABI #58 и успешного Docker Publish закрепить опубликованный ABI SHA в общем `deploy/images.env` отдельным PR.

## 3. Ревью

- [x] 3.1 Упростить OpenSpec/runbook вокруг остановки, выбора окружения, запуска и age-авторизации.
- [x] 3.2 Обновить #109 для ревью и остановиться без merge, Deploy, подготовки данных или авторизации.
