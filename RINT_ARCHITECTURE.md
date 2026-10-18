# Rint on FitTrackee

Rint extends FitTrackee 1.3.5 (upstream commit
`d9cfb15e6d2a5a3523dde7fbd5c098f6fb68357d`) under AGPL-3.0-only.
The existing Flask/PostGIS service remains the authority for accounts,
visibility, activities, media, follows, comments, likes, moderation and exports.
The Vue client remains the web application. Native SwiftUI iOS and watchOS
clients use the same authenticated service.

## Maintenance boundaries

Keep response-status checks and API error handling in
`fittrackee_client/src/store/request.ts`. Store actions own their mutations,
navigation and loading state. Custom response contracts, such as HTTP 204,
remain explicit in their actions.

Translation folders contain JSON sections assembled by `src/locales/messages.ts`.
`src/i18n.ts` loads a selected language once and keeps English as the fallback;
do not import all languages into startup code. Supported language labels and
date locales live in `src/utils/locales.ts`.

Backend scope expectations belong in `fittrackee/tests/test_scope_contracts.py`.
HTTP status and JSON envelope checks share `fittrackee/tests/custom_asserts.py`'s
`assert_response`. Named fields use exact equality; `contains` is reserved for
contracts that explicitly permit substring matches. Keep domain and authorization
assertions in their scenarios rather than deriving expectations from application
code.
The compact regression suite prioritizes security boundaries and critical user
workflows. Email delivery tests retain an independent password-reset expectation;
the exhaustive rendering snapshots have been removed. Add related assertions to
the appropriate scenario with a useful failure label. Keep separate scenarios
where fixture or transaction isolation matters. See [test scope](TESTING.md) and
[validation commands](RINT.md#validation).

## Activity contract

Original recordings are retained. A versioned, device-independent stream stores
elapsed seconds, cumulative metres, optional GPS, heart rate, cadence, power,
altitude, recording state and device laps. GPS is optional. Calculations run in
`rint_core`; browser and Apple clients display server results rather than
implementing competing formulas. Missing values remain missing. An activity's
sport and provenance stay attached to its results.

Imported activities default to private. Explicit sharing uses FitTrackee's
existing visibility rules. Analysis APIs never expose owner-only streams to
other accounts. Public views retain only permitted sensor fields and redact
route endpoints on the server, including chart coordinates and photo metadata.

## Migration

A Strava archive is staged without extracting untrusted paths. CSV metadata is
matched to supported recordings and photos. Preview shows errors and duplicates
before import. Per-item transactions, file digests and source identifiers make
retries idempotent. Progress is persisted; a failed item can be retried without
reimporting successful activities. Originals remain downloadable.

## Apple clients

HealthKit owns native workout sessions and Apple Health persistence. Core
Location supplies outdoor routes. WatchConnectivity transports completed
recordings to the phone, using persistent queued transfers and acknowledgements.
The phone maintains a durable upload outbox keyed by workout UUID. A recording
is retained until the server acknowledges it; server deduplication tolerates
repeated deliveries. Watch recording works without a nearby phone.

Server upload and Apple Health persistence have independent durable queues.
Server acknowledgement cannot discard an unfinished Health save. A retry finds
the workout by stable sync metadata, reconstructs the full route from the saved
draft in bounded batches, and retains failures for another attempt. Reconstructed
Health workouts retain distance, energy and events; missing Health sensor writes
are not invented. The original Rint sensor stream remains available.

Credentials are stored in Keychain. Deployment uses HTTPS. Health permissions
are requested in context; declining a permission leaves the corresponding
field unavailable. Simulator compilation does not establish physical-device
recording, battery, sensor, recovery or synchronization reliability.

Apple history uses an account-scoped journal, anchored 50-workout pages and a
content-addressed outbox. `rint_health_workouts` retains independent Health source
identities/snapshots linked to the existing Workout, rather than making a second
activity store. Source sync identifiers handle replacement Health UUIDs; Rint
recording metadata handles either Health/Watch delivery order. Similar existing
activities require an explicit duplicate decision. Later measurements enrich the
same analysis and geometry while preserving sharing and original files. See
[Health architecture and limitations](RINT_HEALTH.md).

## Implementation order

1. Deterministic stream parsing, splits, best efforts and numerical tests.
2. Persisted migration preview/import/retry and authenticated analysis APIs.
3. Mobile analysis, migration screens and social-feed improvements.
4. Native iPhone/watch recording, Health import, durable sync and native charts.
5. End-to-end validation, deployment instructions and physical-device checklist.

Keep federation, multisport parsing and heatmap changes compatible with the
upstream provisional roadmap rather than replacing upstream implementations.
No metrics, charts or exports have subscription checks.

## Upstream review and compatibility

Reviewed the stable 1.3.5 source and provisional roadmap on 2026-10-10.
Sources: [upstream repository](https://codeberg.org/FitTrackee/FitTrackee),
[roadmap issue 1010](https://codeberg.org/FitTrackee/FitTrackee/issues/1010),
and [federation pull request 679](https://codeberg.org/FitTrackee/FitTrackee/pulls/679).
The roadmap places FIT statistics, multisport/triathlon, heatmaps and per-sport
privacy in 1.4, federation in 2.0, and indoor/UI improvements in 3.0. These are
upstream's provisional plans, not promised release dates.

Reuse authentication, uploads, account export, permissions and social moderation.
Keep new stream/import tables additive and calculation code independent of Flask.
The native UUID upload contract avoids a competing activity store. Before upstream
contributions, rebase against its development branch and propose the stream
contract and reproducible calculation tests as small changes. No upstream author
has been contacted and no contribution has been submitted in this implementation.

## Material tradeoffs and release state

The first complete web path is ZIP preview → private activity → analysis and
exports → explicit sharing and comments/likes. Native apps compile and retain
workouts offline, but physical reliability is a separate acceptance gate.

Canonical and calculated JSON simplify auditability and client consistency at the
cost of storing both representations. Bounded numerical processing handles a
50,000-sample/200 km fixture in about 0.8 seconds on this development machine.
Very large archives currently process five activities per request rather than
using the worker; per-activity commits and a transaction advisory lock support
safe resume. A future worker should use the same persisted manifest and locks.

Independent Watch recording uses HealthKit and durable WatchConnectivity file
delivery. It does not mirror a live session onto the phone. iPhone HealthKit
recording requires iOS 26; supporting older versions needs a separate recorder.
Native charts use Swift Charts; web charts render the same server stream with
touch inspection, zoom, interval queries and comparison.

Native protected maps, interval/comparison controls, community profiles,
follow requests, inbox, moderation and privacy/unit preferences are implemented.
Earlier FitTrackee originals can be backfilled into `rint_analysis_cache` in
resumable batches, preserving source files and endpoint protection. Route-level
web modules and selected language packs load lazily. The current production main
JavaScript chunk is approximately 1.00 MB minified (327 KB gzipped), down from
1.72 MB before language loading was consolidated. These figures describe the
main chunk; maps, charts and password dictionaries have separate chunks.

Outstanding work includes physical recording/battery/Health-save acceptance,
native push delivery and full touch/picker acceptance, large real export validation and per-leg multisport. WatchConnectivity
file delivery cannot be proven in Simulator; the observed recording-to-server
check used a deliberately manual synthetic handoff.
Docker configuration passes the official Compose schema; a runtime build was
not possible because Docker is absent. Development PostGIS and both new schema
migrations plus the distance-column migration have been exercised locally.

When distributing or hosting this modified AGPL service, make the corresponding
source of this fork available to its users. The upstream source link alone does
not describe these modifications. Publish this fork or provide a complete source
archive alongside the hosted service. See the preserved LICENSE for its terms.

Native photo attachment and profile photos reuse the upstream multipart media/
picture APIs. They decode to a maximum 2,048-pixel JPEG with source metadata
removed, preview before uploading, preserve existing attachments and audiences,
and reuse the uploaded media ID when attaching fails. Full account export reuses
the existing server export jobs; iOS streams the ZIP to a protected local file
for the system share/save sheet. No subscription check is introduced.
