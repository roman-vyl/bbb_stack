## 1. bbb_stack

- [x] 1.1 Add `JOURNAL_ABI_BASE_URL: "http://abi:8787"` to `journal-service` in `docker-compose.yml`; no `depends_on`.
- [x] 1.2 README paragraph about the Central Journal.
- [x] 1.3 Rendered `journal-service` environment shows the five `JOURNAL_*` values and no other change against main (check only that service; never print the whole rendered config).

## 2. Rollout (on the owner's word only)

- [x] 2.1 PR and merge.
- [x] 2.2 Separate PR: `JOURNAL_IMAGE` pin to the journal_service image with the builder.
- [x] 2.3 Deploy on the owner's word, after checking every pin in `deploy/images.env` against what the Mac runs.
