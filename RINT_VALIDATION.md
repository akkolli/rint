# Evaluation release validation — updated 2026-10-16

## Feed composition — October 16

430 web tests pass across 24 files; lint, types and production build pass.
The iPhone simulator suite executes 31 tests: 28 pass and three opt-in tests
skip. Browser layouts were checked at 320/390/1280 pixels. Native Light, Dark
and Accessibility Medium text were inspected and captured. Actual card-body,
avatar, Like/undo, Comment and private Share navigation were operated across
the browser/simulator checks. No physical device was tested or updated.
[Measurements, screenshots and limits](docs/rint-polish/feed-layout-2026-10-16/README.md).

## Copy cleanup — October 16

Web lint, types and production build pass; the iPhone simulator build including
Watch passes. Actual native/web checks confirm the shorter feed, effort,
recording, Health and record labels, with exact effort navigation preserved.
No full test suites or physical-device checks were repeated for this copy pass.
[Evidence and scope](docs/rint-polish/copy-2026-10-16/README.md).

## Useful information density — October 15, simulator/browser round

425 web tests pass; lint, types and the production build pass. The iOS simulator
suite executes 30 tests with 27 passing and three opt-in skips. iPhone and Watch
simulator builds succeed. No physical device was tested or updated.

Actual browser checks cover the compact feed, activity metrics/map/chart,
direct chart selection, exact effort intervals, weekly selection, records,
private sharing, CSV export, light/system appearance and 320/390/1280 layouts.
At 390 pixels, metrics start 397 pixels earlier and the 220-pixel activity plot
starts 274 pixels earlier. Split rows are 45 pixels tall and retain 44-pixel
inspection targets. Actual before/after evidence uses the same synthetic data,
viewport and scroll position.

The running Watch simulator retained the same 00:28 active / 0.08 km paused
workout through app replacement/relaunch. The new glance layout, resume, lap,
finish confirmation and durable Saved on Watch summary were operated. This is
local recovery evidence; Simulator does not prove Watch-to-phone transfer.
After the Mac was unlocked on October 16, the final iPhone activity, effort,
record, weekly and recording screens were inspected and captured in light,
dark and Accessibility Medium text. The review corrected a vertical effort-row
separator, overlapping enlarged chart axes and a weekly trend hidden by bars.
Repeated chart taps and exact effort navigation updated linked readouts.

A synthetic indoor phone workout started, paused, marked a lap and recovered
after process termination/relaunch with Paused, 0.05 km and Lap 2 retained.
Resume/finish confirmation produced a 00:25 active / 01:09 elapsed / 00:44 paused
summary marked Saved on this iPhone and Synced to Rint. Its activity charts and
Only me sharing editor opened successfully. No external publication occurred.
The simulator was restored to Light and Large text. Native drag/scroll input
remains unreliable in this automation, so exhaustive off-screen accessibility,
finger scrubbing and real hardware reliability are not certified.

[Full comparisons, workflows and limitations](docs/rint-polish/density-2026-10-15/README.md).

## System dark mode — simulator/browser round

425 web tests across 23 files pass, with passing lint, type checks and production
build. Five new checks cover live system-theme changes, cached-page recovery,
manual overrides, listener cleanup and preservation of unrelated preferences.
Fourteen targeted backend signup/preference tests pass. The iOS simulator suite
executes 30 tests with 27 passing and three opt-in skips, including text/metric
contrast checks for both system palettes.

The actual web feed, route map, power chart, weekly trend and records were
inspected at desktop and 390 × 844 sizes. Light/Dark/System were saved through
the running preferences form; System resolves to the browser's current dark
appearance. Live OS-change events are covered by automated media-query tests;
the Mac's global appearance was not changed. The demo account was restored to
System. The user's own account now uses System, and the existing private HTTPS
web server serves the latest interface scripts and styles successfully.

After the Mac was unlocked, the running iPhone 17/iOS 27 simulator switched
light → dark → light without restarting Rint. Native feed, geographic route,
activity metrics, chart selection, weekly progress, records and recording-ready
screens were inspected and captured. An activity-chart tap changed the linked
readouts to 16:45, 3.62 km, 147 bpm and 289 W; a weekly-chart tap changed the
summary from the current 6.5 km week to 30.0 km and eight workouts. The simulator
was restored to its original Light appearance. Watch's system appearance
setting is unsupported, and its existing native dark interface is unchanged.
No physical devices were tested or installed. These appearance checks do not
certify hardware recording, background synchronization or battery use.

Screenshots and scope: [dark-mode review](docs/rint-polish/dark-2026-10-14/README.md).

## Tap interaction and information density — simulator/browser round

The October 14 refinement adds direct and persistent chart selection, weekly
trends, contextual Records, recorded-power route colours and broader feed hit
areas. It fixes the web route wrapper's missing event/unit forwarding, removes
empty content panels and compacts native sharing. Actual simulator/browser
workflows and before/after evidence are recorded in
[the interaction review](docs/rint-polish/interaction-2026-10-14/README.md).

420 web tests pass; lint, types and production build pass. Native has 26 passing
tests and three opt-in skips; simulator/companion builds succeed. Repeated taps,
record-to-effort navigation, route-linked values, missing power, independent web
social controls, private sharing and a free CSV download were operated. Browser
layouts were inspected at 320, 390 and 1280 pixels.

This round uses no physical devices. Native drag/scroll automation was
inconclusive, and the Mac lock prevented the last native bar/clipping screenshot
recheck. Earlier physical installation and recording checks below are historical;
they do not certify this round's native changes. The current native refinements
are in source and simulator builds, not a newly deployed phone/Watch release.

## Weekly mileage, activity details and records — October 14

- Web: 416 tests across 19 files pass; lint, types and production build pass.
  Rint backend: 42 tests pass. iPhone simulator: 23 tests pass, with three
  opt-in integration/fixture checks skipped. Latest signed simulator and signed
  iPhone/Watch Release builds succeed. These counts do not mean every workflow
  has been validated on physical hardware.
- Weekly history uses local Monday boundaries and the entire account history.
  Automated coverage includes timezone/DST boundaries and account isolation.
  The actual personal server returns 35 weekly buckets and seven sport-specific
  all-time records, with zero original recordings awaiting analysis. The user's
  93 recordings remain in the separate private database.
- Actual running iPhone simulator checks: Home → Week → Records → 5 km source
  workout → exact highlighted interval; per-workout bests → 1 km interval;
  geographic MapKit route → full-screen streets; sharing editor → native share
  sheet → unchanged private audience. There was no external message or post.
  Returning from a workout now preserves the selected Progress section.
- Actual running web checks: Week/Records, direct record-to-workout interval,
  per-workout efforts and all-time badge, geographic tiles, map expansion,
  keyboard focus containment and Escape restoration. Reviewed at desktop,
  390 px and 320 px widths. Evidence uses synthetic demo activities.
- The actual 6.03 km imported personal run's pace calculation was checked
  locally: the prior maximum of approximately 150 min/km becomes 14.2 min/km
  with the 30-second display window, and no readings are clipped by the focused
  scale. This is actual-data calculation evidence, not a physical touch test.
  The raw data stays private and original recordings are unchanged.
- Watch simulator: start, pause, resume, lap feedback, explicit controls,
  finish confirmation, durable summary and offline-retention text were operated.
  A longer check found paused time/distance advancing under simulated sensor
  input. Checkpointed timing and distance anchors fix that issue. A fresh
  recording stayed at 1:14 and 0.12 km while paused, including after termination
  and relaunch. Automated coverage verifies paused clock/distance recovery and
  non-regressing phone/server receipts.
- Final build 3 passes matching companion metadata, deep signature verification
  and profile membership checks for both selected devices. It was installed
  successfully over the existing app on the user's selected iPhone and paired
  Watch. Private HTTPS and the reloaded personal server remain healthy. The
  connection briefly dropped during the first Watch attempt; retry succeeded.

Screenshots and workflow notes: [October 14 evidence](docs/rint-polish/2026-10-14/README.md).
Logs: `/private/tmp/rint-oct14-{backend-tests,web-tests,web-lint,web-build,native-tests,device-build}.log`.
Installation logs: `/private/tmp/rint-oct14-{phone,watch}-final-install.log`.

**Still requires physical-device validation:** a complete Watch file-transfer
and server acknowledgement, fresh Health permission flows, outdoor GPS accuracy,
background interruptions over a long workout and battery use. Apple explicitly
states that Simulator does not support
[Watch Connectivity file transfers](https://developer.apple.com/documentation/watchconnectivity/wcsession/transferfile(_:metadata:)).
The simulator summary therefore retains its Watch copy and does not pretend it
has synchronized. Native push delivery still needs APNs/distribution setup;
in-app notification badges work, but they are not push notifications. Registration
remains closed on the private server and invitations explain that limitation.
The existing web bundle-size warning remains; exhaustive VoiceOver and
slow-network/performance acceptance are not claimed.

The source remains AGPL-3.0-only, with free metrics, charts and exports. These
changes resolve the primary mileage/records/map/activity-detail shortcomings;
they do not constitute a claim of complete Strava feature or reliability parity.

## Personal HTTPS server and physical installation — October 11

- The separate personal server runs in production mode at port 5081, with its
  own `rint_personal` database, upload directory, Redis database and export worker.
  A macOS login service supervises the web and worker processes. The existing
  demo at port 5080 remains healthy and separate.
- Tailscale Serve provides private HTTPS to the personal server. Normal TLS
  certificate verification succeeds; root, ping, database and configuration
  endpoints return HTTP 200. The Serve configuration has no public Funnel.
  The actual HTTPS registration page was opened in the browser. The Mac must
  remain awake, logged in and connected; reboot recovery and backup restoration
  have not been validated.
- iOS/watchOS Release builds succeed with the user's Apple development team.
  Both signatures verify; provisioning includes HealthKit and the iPhone's
  background delivery entitlement. The native build prefills the personal
  server URL without storing it in shared source.
- `devicectl` confirms Rint installed on the selected physical iPhone 18 Pro Max
  running iOS 27.0.1. Developer Mode is enabled. The latest corrected companion
  package was installed successfully and `devicectl` successfully launched Rint
  on the phone. User sign-in and visual confirmation are still pending.
- Watch pairing and provisioning were repaired as described below. The corrected
  signed companion is embedded in the installed iPhone app. After the user kept
  the Watch awake, direct installation succeeded. `devicectl` confirms version
  1.0.0/build 2 on the physical Watch and successfully launched its app.
- The user's registered personal account is activated and verified as owner.
  No real Health history was imported by the installation agent. Device workflow
  checks remain pending. Physical
  installation is not evidence of recording, Health, transfer or battery quality.

**Watch installation follow-up:** the iPhone Watch app returned to Install after
its progress circle completed. The actual packaged bundles were missing both
version fields despite source plist defaults. Explicit shared marketing/build
settings now produce version 1.0.0/build 2 for both targets. The signed replacement
was installed over the existing iPhone app; device inspection confirms build 2.
`scripts/rint-check-apple-bundle.py` passes against that built app and rejects a
missing-version regression fixture. The Watch installation still rolled back
after this correction, so missing metadata is not claimed as the sole cause.

Fresh pairing now confirms a physical Watch Ultra 3 running watchOS 27.2,
Developer Mode enabled, connected to the Mac over the local network. The old
26.5 record was stale; only its Mac development pairing was replaced, preserving
the Watch–iPhone pairing. Direct installation then exposed a concrete signing
failure: `0xe8008012`, because the Watch profile did not contain the Watch UDID.
Building for the actual Watch registered it and regenerated the profile. A clean
Watch build was required to replace a stale incremental signature after the
profile changed. The rebuilt phone and embedded Watch pass deep signature
verification and profile membership checks for both real devices.

The packaging helper now accepts `--phone-udid` and `--watch-udid`; the actual
Watch profile passes and an unregistered-device fixture is rejected. Ruff and
format checks pass. Two subsequent installation attempts failed with CoreDevice
4000, RemoteServiceDiscovery connectivity unavailable, and Device Hub showed the
Watch disconnected. Once the user kept it unlocked and awake on the same Wi-Fi,
direct installation succeeded. Device Hub lists Rint 1.0.0 on the physical Watch;
`devicectl` confirms build 2 and successful launch. The mirrored Watch display
remained black, so this is installation/launch evidence, not visual acceptance
of the running app. No physical workout or Health permission flow was exercised.
The corrected phone
package was installed successfully and launched on the selected physical iPhone.
Logs: `/private/tmp/rint-watch-registered-clean-build.log`,
`/private/tmp/rint-watch-registered-install-retry.log`,
`/private/tmp/rint-watch-awake-install.log`,
`/private/tmp/rint-phone-watch-registered-build.log`, and
`/private/tmp/rint-phone-watch-registered-install.log`.
The actual Device Hub installation screenshot is saved privately at
`.local/personal/watch-installed.png`.

Logs: `/private/tmp/rint-device-signed-build.log`,
`/private/tmp/rint-iphone-install.log`, `/private/tmp/rint-watch-install.log`.
Private server logs/configuration and the HTTPS-page screenshot are under
`.local/personal/`, excluded from Git. The hosting helper passes Ruff and syntax
checks. Earlier simulator test results below are unchanged by this installation.


## October 11 product structure pass

- Web build/types pass; 414 unit tests across 19 files pass. Four new checks
  cover training aggregation across a year boundary, loading failure/retry, and
  initial/paginated feed recovery without skipping a failed page.
- Rint backend: 41 tests pass against isolated `rint_test`, including new
  route-presence metadata respecting map permissions. Existing import,
  idempotency, metrics, export and privacy tests were rerun.
- iPhone simulator: build and test succeed; 21 executed, 18 passed and 3 opt-in
  fixture/transport tests skipped. The latest native route preview changes are
  included. The subsequent unlocked simulator review below supersedes the earlier
  visual-testing limitation. Physical-device validation remains deferred.
- Running browser checks: profile → selected Health workout, heart-rate chart,
  kilometre/mile conversion, sharing disclosure, unchanged private visibility
  and 1500 m endpoint protection saved, activity link copied, Add → Strava
  correctly selects the archive importer, Health choice exposes `rint://health`.
- Responsive/keyboard: 390 px phone, 320 px phone and desktop reviewed. Dark
  appearance and Escape dismissal restore focus to the account menu. The annual
  chart shows all twelve months on the smallest viewport.
- Build reports the existing large main-bundle warning. These checks do not
  establish full accessibility, slow-network performance, battery reliability,
  or Strava replacement readiness.

Evidence: `docs/rint-polish/product-2026-10-11/`; rationale and before/after images
are in `RINT_DESIGN.md`. Latest logs are `/private/tmp/rint-product-web-tests-final.log`,
`rint-product-backend-tests.log`, `rint-product-native-final-tests.log`,
`rint-product-web-final-build.log`, `rint-product-lint-final.log` and
`rint-product-format-final.log`.

This records the current implementation and simulator review. It is not a
daily-use or physical-device acceptance sign-off, and does not claim that every
Strava design/UX gap is closed. Tests use synthetic activities and public
recording fixtures; no personal Strava export or physical Apple device was used
in those earlier tests. See the subsequent device-installation evidence above.
The source baseline remains FitTrackee 1.3.5, under AGPL-3.0-only.

## Unlocked native review — October 11 afternoon

The actual iPhone 17/iOS 27 app was reviewed after the Mac unlocked. Native
coordinate input recovered on iPhone, including tab taps and direct chart drags.
These are running-app checks, separate from compilation and unit tests.

**Corrections made from visible findings:**

- A pair of isolated GPS fixes produced a database geometry but no drawable
  preview. Both feeds now reserve media space only for an actual connected route
  section, respecting map/analysis permissions and endpoint protection. A compact
  route note replaces the empty panel. Regression coverage includes separated
  fixes, sampling gaps and a wholly protected route.
- Native feed actions have comfortable spacing and named profile controls.
  Comment opens the conversation directly. Owner Share opens privacy controls.
  Returning to the feed retains its activity position.
- Activity details hide the tab bar, put sharing in the navigation bar, move
  comparison below the main chart, and show only available sensor choices.
  Selection begins at a real reading. Changing metrics preserves an inspectable
  time or selects that metric's first reading when the old time has no sample.
- Imports & data puts Health and Strava first, followed by exports, sync status
  and account controls. Sign-out has a confirmation explaining retained uploads.
  The Health screen uses a compact task heading. Changed history filters disable
  import until reviewed; empty status rows are omitted. Training shows all twelve
  months without horizontal scrolling.

**Actual workflows checked:**

1. Feed → Health workout → pace/heart-rate selection. Direct chart dragging
   changed the cursor and reading (04:19 / 131 bpm on the synthetic 15-minute run).
   An accessible slider action alone initially moved the thumb without updating
   its reading; the subsequent actual drag did update it. This is not a VoiceOver
   acceptance result. New native before/after and chart screenshots are saved.
2. Comment → conversation, back → same feed activity, Share → saved audiences.
   The original Health activity retained private activity/map visibility and a
   1,500 m radius. Saving unchanged settings succeeded. The system link share
   sheet opened; no message was sent. Samples CSV preparation completed and
   exposed its Save or share export action.
3. You tab → athlete home → Imports & data → Health. Disabling all-history
   exposed the date picker and disabled import with an explanation; restoring
   the saved selection re-enabled it. The actual Check for missing workouts
   action displayed progress, then completed with zero queued uploads.
4. The first rescan found a previously unimported 56-second simulator workout
   (0.161 km), so the account changed from 10 to 11 activities. Existing Watch
   recordings linked to their Health records. A second rescan left 11 activities
   and four Health identities: no extra activities. The original 4.800 km Health
   run retained its audience and protection settings. The new imported activity
   opened with pace, heart-rate and power charts despite having no drawable GPS
   route. Switching to heart rate in the final build selected its first reading
   at 00:05 / 125 bpm rather than a preceding unsampled time. All data are synthetic
   simulator fixtures.
5. Record tab ready state, Progress with all twelve months, profile navigation,
   and feed actions were visually inspected. Watch ready and sport-list screens
   were captured. Recentring the Watch window allowed the sport list to open;
   the attempted selection return did not visibly complete. No new Watch recording
   or transfer acceptance is claimed in this increment.

Latest native suite: 21 executed, 18 passed, 3 opt-in fixture tests skipped.
Backend: 41 passed; changed Python files pass Ruff and preview-module Mypy.
The workouts model still has its previously documented upstream Mypy error in
`convert_value_to_integer`; the new route-presence code adds no type errors.
The unchanged web suite's last result remains 414 passed. The running web feed
was reloaded at phone size to verify the shared route fix. Logs:
`/private/tmp/rint-unlocked-native-final.log`,
`/private/tmp/rint-unlocked-backend-tests.log`,
`/private/tmp/rint-unlocked-types.log`.

Screenshots are unaltered CUA captures in
`docs/rint-polish/product-2026-10-11/` (`native-*` and `watch-*`). Earlier screenshots
show ten demo activities; those after the Health rescan may show eleven.
Full physical recording, battery use, real Health permissions, VoiceOver, Dynamic
Type and WatchConnectivity transfer remain outside this simulator evidence.

## Current automated results

| Check | Result | What it establishes |
| --- | --- | --- |
| Rint Python suite | 41 passed | Numerical/migration coverage, Health identity/enrichment/retries, source exports, duplicate review, privacy, bounded feed previews, sharing round trips, legacy bests backfill, equal-timestamp sensors and old Health-analysis repair |
| Vue unit suite | 414 passed in 19 files | Utilities, peak/gap chart handling and awaited follow-request acceptance/failure |
| Web production build/types/lint/format | Passed | Production assets compile, Vue types and both lint tools pass, source formatting checked |
| Python lint/types | Passed | Ruff checks core/backend/tests; Mypy checks all 8 Rint backend modules |
| Ordinary native simulator suite | 18 passed; 3 opt-in tests skipped | Recording/chart units, Health identity/jobs/events/sports/review/outbox, API decoding, independent distance anchors, duration rounding, photo metadata removal and independent Health-save persistence |
| Actual Health SDK fixture reader | 1 passed separately | Synthetic Watch provenance, 4,800 m distance, at least 30 heart-rate and route samples |
| Native Health-to-local-server rescan | 1 passed separately | Real reader/journal/outbox/API, same activity ID and count, 4.80 km, retained HR, private sharing and 1,500 m route protection |
| Native account/photo/export transport | 1 passed separately | Real iOS profile save, photo attachment with unchanged privacy, and ZIP download from the local synthetic account |
| iPhone/Watch simulator targets | Built successfully | SwiftUI targets compile with local ad hoc simulator signing |
| Database upgrade | Applied locally | Health identity and legacy analysis-cache migrations succeed on development PostGIS |

Integration tests use isolated PostgreSQL 17/PostGIS and Redis, with real database
persistence. Native tests use iPhone 17/iOS 27 and Xcode 27 beta; Watch review uses
its paired Ultra 3 (49mm)/watchOS 27 simulator. Simulator HR/GPS are synthetic.
Successful builds and unit tests do not prove physical recording or synchronization.

The following checks retain results from earlier stages; they were not rerun
for every UI change: combined media/map suite 52 passed; upstream comments/likes
123 passed; timeline/account-export/media serialization 96 passed; Health plus
account-export suite 84 passed; Compose configuration passed the official schema.
The full upstream Python suite was not run.

Whole-project Mypy previously reported eight errors in unchanged upstream code
(users/models.py, workouts/models.py, workouts/utils/workouts.py), reproduced
against the original checkout. New Rint modules pass. Production npm dependency
audit previously reported zero vulnerabilities; four development-only high
findings remain in the ESLint/fast-glob/micromatch/braces chain.

## Running web workflows

Reviewed at 1365 × 900, 390 × 844 and 320 × 740. The earlier complete path imported
a synthetic Strava ZIP, opened its feed card, scrubbed HR, inspected splits/bests,
compared activities, analyzed an interval, saved follower sharing with a private
map, copied a privacy-aware link and downloaded a samples CSV. A repeated archive
returned three duplicates with no new activities. Likes and a private comment
were saved through the web UI.

This increment reviewed the data hub, protected sharing, directory, athlete
profiles, account navigation, notifications and training history. A synthetic
Health activity appeared in the feed, provided HR/pace/elevation charts and
splits, and exported its samples. Its private activity/map audiences and 1,500 m
radius survived a reload and appeared identically in native sharing.

The follow-request workflow revealed a real race: the inbox refreshed before
acceptance finished. It now waits for server success, disables both controls
while pending, and retains the request on failure; two regression tests pass.
Feed time labels now round fractional seconds once, including minute/hour carry,
and activities without a shared route use a compact summary rather than a large
empty map panel. The directory fixture was corrected to use the actual persisted visibility field.
New-page navigation now resets scrolling while back navigation restores position.

Route modules load lazily, reducing the main bundle from about 2.27 MB to 1.72 MB
uncompressed (about 579 KB gzipped). The remaining large-chunk warning is real;
slow-network first-load performance is not signed off. Dense tables scroll within
their own containers. Light/dark appearances were checked; comprehensive keyboard,
screen-reader and browser/device coverage remains open.

## Actual native and Watch workflows

The signed iPhone simulator completed login, live feed/activity review, chart
metric selection, Health permissions/history import and sharing-settings review.
A separate SDK test reads the synthetic 15-minute Health workout. Its native
rescan-to-server test caught two accuracy issues: standalone Health quantity
samples were missed, and equal-timestamp sensor/route merging dropped distance.
Both are fixed. The same activity now has 4.80 km with preserved HR and privacy,
without another activity. Older derived Health results repair from retained
sources on analysis/preview access; original files remain unchanged.

The Watch received account, sports and units through application context.
Start, pause, resume, mark lap and finish were exercised in its actual UI.
An initial 56-sample recording and two lap intervals persisted after relaunch.
That recording exposed stale distance being written by sensor callbacks. The
recorder now writes independent distance anchors only when distance is measured,
plus explicit pause boundaries. A fresh actual UI recording retained 89 samples
and 26 distance anchors: 107.24 m, 52.34 s elapsed, 41.06 s active, 11.28 s paused
and 37.26 s moving, with two laps. The updated ready screen has a separate sport
list with the current sport first and returns to Start after selection.

Apple explicitly states that [WatchConnectivity file transfers are unsupported
in Simulator](https://developer.apple.com/documentation/watchconnectivity/wcsession/transferfile(_:metadata:)).
The recording was deliberately copied into the phone's outbox as a synthetic
fixture. Both completed fixtures reached the phone’s actual background uploader with
HTTP 201 and produced one local activity per recording. The fresh recording
appeared in the native feed as 0.11 km and 00:37 moving time. The Watch original remains retained. This proves the phone/server path
for that file, not Watch-to-phone transfer or server-ACK delivery to Watch.

Native profile editing (names, location, bio, birthday and photo), photo
attachment/preview/retry and full-account export/status/download screens are now
implemented. The real iOS transport test attached a synthetic photo without
altering existing activity privacy and downloaded a valid account ZIP. Its
archive was prepared using the existing server exporter, not a running worker.
Photo encoding is capped at 2,048 pixels, strips source EXIF/GPS metadata and
retains an uploaded media ID for attachment retries. Native picker/touch and
profile-photo acceptance remain unverified. The running simulator also saved the
loaded profile, downloaded the 1.5 MB archive and opened the iOS ZIP save/share
sheet. The attached fixture displayed in its native gallery. System photo and
Files pickers opened, but exposed no actionable accessibility controls; selecting
an image was blocked by the coordinate-input limitation. A regression fixes an upstream bug
that cleared location whenever a bio was blank. Web photo buttons now have
accessible names and respond to Space and Enter; Space opened the actual gallery.

Native comparison selection was exercised with the Health run and park loop.
The actual chart exposed a false connecting line and lost comparison styling.
Distinct String section identifiers and explicit workout colour grouping fixed
it; a rebuilt simulator showed independent solid violet and dashed amber traces.
Comparison loading, missing samples and retry now stay beside the chart. Interval
results clear on bounds changes, and outdated responses cannot populate a new
selection. The default whole-workout interval returned 4.80 km/15:00/133 bpm;
changing its bounds via touch/drag remains unverified. Screenshots record the
rendering defect and correction.

Independent Health-save jobs now survive server acknowledgement and can retry
workout/full-route persistence. Native maps, interval/comparison controls,
profiles, follow requests, moderation, inbox and preferences are implemented and
compile. They are not all accepted through touch UI: iPhone coordinate/drag
control reported missing windows while semantic button actions continued to work.
Accessible scrolling recovered on native Form/List screens.
At that earlier stage, a full iPhone scroll/drag/tab-navigation pass remained
unverified. The Mac locked again at the end of that session; the unlocked review
above now covers direct chart dragging and tab navigation. The final native
build and ordinary tests passed and the app relaunched, but the final added
comparison loading/retry and interval-state changes could not receive another
visual pass after that lock. The comparison-rendering screenshots were captured
from its preceding successfully rebuilt fix. System Health screens on watchOS 27 beta also displayed localization
keys; those are Apple system strings, not Rint copy.

## Open product and release gaps

* Physical recording, Health history/permissions, offline Watch transfer,
  interrupted-session recovery, complete Health persistence, background scheduling
  and battery use remain unverified. The user explicitly deferred physical checks.
  Follow [DEVICE_TESTING.md](apple/DEVICE_TESTING.md).
* The signing team and private HTTPS server are now configured and iPhone
  installation succeeded. Watch installation and physical workflow acceptance
  remain open. TestFlight/App Store distribution has not been configured.
* Native push delivery remains incomplete. An in-app inbox is implemented, but
  it is not push delivery. Photo attachment, profile editing and account-export
  screens now exist and pass transport checks; their full native touch/picker
  acceptance remains open. Account credential changes still use the web.
* Complete the remaining native touch, VoiceOver, Dynamic Type, photo/privacy and
  multi-user workflow review. Simulator button actions do not prove ergonomics.
* Validate large personal exports and interrupted archive upload. Processing
  resumes after a complete ZIP upload; archive upload itself is not resumable.
  Background migration workers and per-leg multisport are still outstanding.
* Build/run the Docker stack, verify upload-volume ownership and restore a backup.
  Docker is unavailable here; schema validation does not establish deployment.
* Further reduce initial web payload and measure performance on a real phone and
  slow network. Full daily-use reliability and Strava-level social adoption are
  not established by synthetic fixtures.

See [design decisions and screenshots](RINT_DESIGN.md),
[calculation methods](RINT_METRICS.md), [Health details](RINT_HEALTH.md) and
[architecture](RINT_ARCHITECTURE.md). Metrics, charts, personal bests and exports
remain available without subscription checks; the open-source license is preserved.
