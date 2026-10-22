## 1. bbb_stack

- [x] 1.1 Remove `read_only: true` from the Runtime specs mount in `docker-compose.yml`.
- [x] 1.2 README sentence about the Runtime mount.
- [x] 1.3 `docker compose config` shows the specs mount of `strategy-runtime` writable and no other change against main.

## 2. Rollout (on the owner's word only)

- [x] 2.1 PR and merge; the image pin for Runtime and the deploy are separate steps.
  Done: #60 merged; deployed on the Mac on 2026-10-22 with Runtime `a7ab16c`: the specs mount is `RW=true`, an `os.replace` from inside Runtime worked and Research read the same bytes; the owner accepted the work.
