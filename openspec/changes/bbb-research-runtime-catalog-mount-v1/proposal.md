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

## Findings that the checks must settle

1. **Write capability.** A read-write bind mount gives the whole Research container
   write access to every file of the Runtime catalog, beyond the API. The guarantee that
   Research only creates new files rests on Research code and its tests; Runtime's own
   mount stays read-only.
2. **API protection.** The Research API has no authentication of its own. The only
   protection is publishing on `127.0.0.1:8095` and the CORS allow-list. CORS does not
   stop a cross-site simple request: a page open in the owner's browser can send
   `POST http://127.0.0.1:8095/api/research/candidates/<id>/runtime-export` with no body
   and no custom headers, and the route would run (the response is unreadable to the page,
   but the file is created, disabled). The impact is a new disabled file for an existing
   candidate id, but it is a hole in the "protected route" requirement. A fix belongs in
   research_service (for example requiring a custom request header or a JSON content type
   on this route) and needs the owner's decision; this change only makes the check a
   recorded step.
3. **Mac filesystem.** `flock` and `os.link` on a Docker Desktop bind mount are not
   guaranteed; they are verified on the real mount before use.
