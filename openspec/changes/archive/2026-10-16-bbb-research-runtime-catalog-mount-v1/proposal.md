## Why

Research Service gets a create-only route that writes a candidate's strategy spec into
the Strategy Runtime deployment catalog with `enabled: false`
(research_service `research-candidate-runtime-export-v1`, PR #34, tasks 2.1 and 2.2).
The route needs the catalog directory in the Research container, and the owner needs
evidence that the route is protected and that `flock` and hard links work on the Mac
bind-mount before the feature is used.

Today `${BBB_DATA_ROOT}/strategy-runtime/specs` is mounted only into Strategy Runtime,
read-only. `research-service` mounts only `${BBB_DATA_ROOT}/research` at `/data` and has
no `RESEARCH_RUNTIME_SPECS_PATH`.

## What Changes

- `docker-compose.yml`, service `research-service`: add a bind mount
  `${BBB_DATA_ROOT}/strategy-runtime/specs` → `/runtime-specs` (read-write) and
  `RESEARCH_RUNTIME_SPECS_PATH: "/runtime-specs"`.
- `strategy-runtime` keeps `/runtime/specs` read-only; nothing else about Runtime changes.
- `docker-compose.deploy.yml` needs no change (it overrides only `image`).
- A verification record `docs/verification-research-runtime-export-v1.md`, filled in at
  apply time, with the checks listed in `tasks.md`.
- OpenSpec requirement added to `bbb-live-stack` for the mount and for the API protection
  model.

## Non-Goals

No change to any service repository, no image pin bump (a separate PR after research_service
PR #34 is merged and its image is published), no change to `deploy/images.env`, no new
service, no authentication layer, no change to published ports, no cleaning of the
`loadtest-*` files in the specs directory, no switching of `enabled`.

## Findings that shape the checks

1. **Write capability.** A read-write bind mount gives the whole Research container
   write access to every file of the Runtime catalog, beyond the API. The guarantee that
   Research only creates new files rests on Research code and its tests; Runtime's own
   mount stays read-only.
2. **API protection (known V1 limitation).** The Research API has no authentication of
   its own, and this change adds none and adds no special request headers. Its protection
   is publishing on `127.0.0.1:8095` only, which is a mandatory check (tasks 2.5). A
   cross-site simple request from a page in the owner's browser is a known limitation of
   the local Research API in V1, not a blocker: the export route only creates a disabled
   file for an existing candidate id.
3. **Mac filesystem.** `flock` and `os.link` on a Docker Desktop bind mount are not
   guaranteed; they are verified on the real mount before use.
