# Compact regression suite

This suite prioritizes security and critical user workflows for a single
maintainer. The reduction deliberately drops lower-priority regression coverage;
it does not establish the same coverage as the original upstream suite.
Application features and production code are unchanged by this test reduction.

## Retained boundaries

| Area | Retained checks |
| --- | --- |
| Accounts | Registration, inactive accounts, login/logout, token revocation, password hashing and reset, email changes, account deletion and export ownership |
| Authorization | OAuth authorization/code challenge/token/revocation routes, required API scopes, role escalation and owner-account restrictions |
| Privacy | Owner/follower/public access to workouts, maps, segments, charts and original files; comment visibility and media access |
| Activities | GPX/KML/KMZ/TCX/FIT imports, archive/file limits, upload/read flows, editing, sharing changes and deletion |
| Community | Follow approval/rejection, blocking, timeline visibility, moderation access and suspension/reactivation actions |
| Rint | Metrics, recording idempotency, archive preview, import, Health streams, synchronization and export tests in `tests_rint` |
| Clients | API error handling, login/registration, OAuth, input/file/visibility utilities, locale loading and key Rint components; existing Apple and browser end-to-end tests |

Mocked scope checks complement real authorization tests; they do not replace
them. Rint database integration tests require `RINT_INTEGRATION=1`; a default
test run that skips them is not a complete integration validation.

## Coverage deliberately removed

- Exhaustive serializer snapshots, model representation/getter checks and
  internal service tests overlapping the retained API workflows.
- Permutations of pagination, sorting, chart labels, unit/date/tooltip formatting
  and statistics display.
- Exhaustive notification, email-layout, equipment preference, administration
  configuration and CLI regression cases.
- Unused fixtures, email snapshots and helper methods supporting removed cases.

These areas can now regress without a dedicated test detecting every change.
When fixing a bug there, add a focused regression to an existing scenario rather
than restoring the entire historical matrix.

## Size and execution

`python3 scripts/rint-test-footprint.py` counts nonblank source lines, including
comments, fixtures and helpers, across backend, frontend, Rint, Apple, tooling
and browser end-to-end tests. The baseline is 94,537 lines; the budget is 18,907
lines, an 80% reduction. Binary samples are not source lines. The local backup is
excluded from this maintained suite and from release packaging.

Use the commands in [RINT.md](RINT.md#validation). Run database-backed suites
sequentially because their fixtures recreate the isolated test database.
Apple and browser end-to-end checks still require their respective environments.

A recovery snapshot of the pre-reduction tests is stored locally at
`.local/test-suite-backup/before-compact-suite.tar.gz`. It includes the uncommitted
test refactors present before this reduction and is not uploaded with the repo.
