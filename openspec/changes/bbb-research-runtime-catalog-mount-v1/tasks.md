## 1. Compose (apply)

- [ ] 1.1 `docker-compose.yml`: `research-service` gets the read-write bind mount
  `${BBB_DATA_ROOT:?BBB_DATA_ROOT must be set}/strategy-runtime/specs` → `/runtime-specs`
  and `RESEARCH_RUNTIME_SPECS_PATH: "/runtime-specs"`.
- [ ] 1.2 `strategy-runtime` mount unchanged and still `read_only: true`.
- [ ] 1.3 `docker compose -f docker-compose.yml config --quiet` and the same with
  `-f docker-compose.demo.yml -f docker-compose.deploy.yml --env-file deploy/images.env`
  succeed; the rendered config shows the new mount only on `research-service`, with no
  `read_only` on it, and `/runtime/specs` still `read_only: true` on `strategy-runtime`.
- [ ] 1.4 README: one paragraph on the mount and the variable.

## 2. Verification on the Mac (owner's device, recorded in `docs/verification-research-runtime-export-v1.md`)

- [ ] 2.1 Mounts: `docker inspect` of `research-service` shows `/runtime-specs` with
  `RW: true` and `/data` unchanged; `docker inspect` of `strategy-runtime` shows
  `/runtime/specs` with `RW: false`; a write inside Runtime's `/runtime/specs` fails.
- [ ] 2.2 `flock`: inside the Research container, two processes take `fcntl.flock` on the
  same file in `/data/analysis`; the second fails with `LOCK_NB` while the first holds it.
- [ ] 2.3 Hard links: inside the Research container, `os.link` of a temporary file to a new
  name in `/runtime-specs` succeeds, the temporary file can be unlinked, and a second link
  to an existing name fails with `FileExistsError`; the test files are removed.
- [ ] 2.4 Permissions: a file created in `/runtime-specs` by Research is readable by the
  Strategy Runtime container user.
- [ ] 2.5 API reachability: `curl` to the Research API succeeds on `127.0.0.1:8095` and
  fails on the Mac's LAN address; `docker compose ps` shows no `0.0.0.0` publishing for
  `research-service`.
- [ ] 2.6 Known V1 limitation recorded in the verification file: the local Research API has no
  authentication and no anti-CSRF header; nothing is checked or changed for it here.
- [ ] 2.7 Runtime accepts the exported deployment: for the file just exported by Research,
  `FilesystemDeploymentCatalog.load_snapshot()` run inside the Strategy Runtime container on
  `/runtime/specs` lists that file name among `accepted_deployments` with `enabled: false` and the
  `strategy_instance_id` the export returned, and the file appears neither in `invalid_files` nor
  in `duplicate_identities`. The state of the other files in the catalog (including `loadtest-*`
  and any invalid ones) does not affect this check. The file is not selected for a bar
  (`enabled: false`). Read-only; no state change.
- [ ] 2.8 The existing `loadtest-*` files are listed and left as they are; the owner decides
  separately what to do with them (all are `enabled: true`).

## 3. Out of this change

- [ ] 3.1 Pin bump of `RESEARCH_IMAGE` in `deploy/images.env` (separate PR after research_service
  PR #34 is merged and its image is published).
