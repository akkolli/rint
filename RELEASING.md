# Preparing a Rint release

Rint currently ships as an evaluation beta. Publishing source, deploying the
web service and distributing native apps are separate release steps.

## Source repository

Run `python3 scripts/rint-release-check.py` before staging a release. It checks
tracked and eligible untracked files for local configuration, build artifacts,
root-level personal documents, outside symlinks and a small set of credential
patterns. It prints paths only. It does not inspect Git history or certify that
all private information has been removed. Review the staged diff and history
before the first public push.

Keep `.local`, `.env.rint`, credentials, device exports and generated Xcode
projects out of Git. Generate the native project from `apple/project.yml`.
Retain LICENSE and upstream notices. The backend package still uses its
FitTrackee name/version for compatibility; do not publish it as an upstream
PyPI release.

The current inherited release workflow only runs in `SamR1/FitTrackee`.
`rint-checks.yml` runs source hygiene, frontend lint, tests and build without
publishing. Configure a repository you own as the release destination before
pushing or adding release automation.

## Web deployment

1. Follow [the setup guide](RINT.md#self-host) and generate a private `.env.rint`.
2. Set `UI_URL` to the final HTTPS origin and `RINT_SOURCE_URL` to the source for
   the deployed revision. The latter is a build argument that becomes the
   **Rint source code** link on About. Direct frontend builds use
   `VITE_RINT_SOURCE_URL` instead. Rebuild after changing it.
3. Complete a clean Docker build and smoke test: registration/login, upload,
   activity analysis, private media, export worker and a database/uploads
   backup-and-restore round trip. Docker execution remains unverified locally.
4. Review the instance's registration policy, contact details and privacy text
   before inviting people. Database and Redis stay on the internal network;
   the web port remains bound to localhost behind your HTTPS proxy.

Production images exclude local data and review screenshots and include the
project license. Do not reuse the synthetic development account as a live account.

## iPhone and Watch

Build from `apple/project.yml` with your own signing configuration. Check the
built phone and embedded Watch metadata with
`scripts/rint-check-apple-bundle.py`. Keep signing credentials and archives
outside the source release.

Complete [physical-device acceptance](apple/DEVICE_TESTING.md), including
background recording, recovery, Health permissions, sync, battery use, sound
and haptics. Current simulator results do not establish those outcomes. Store
submission assets, distribution signing and final release identity still need
to be supplied by the publisher.

## Local checks

```sh
python3 -m unittest discover -s scripts/tests
python3 scripts/rint-release-check.py
npm --prefix fittrackee_client run lint-check
npm --prefix fittrackee_client run test:unit -- --run
npm --prefix fittrackee_client run build
```

See [validation](RINT_VALIDATION.md) for backend and native checks and remaining
limitations. Do not interpret a successful source check or UI build as a
completed production deployment test.
