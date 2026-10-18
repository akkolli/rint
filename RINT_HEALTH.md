# Apple Health history and automatic sync

The native iPhone app imports workouts accessible through HealthKit, including
Apple Watch workouts shown in Apple's Fitness app. Browser HealthKit access is
unavailable: use the phone for import/sync, then view the same activities, free
charts and exports in the phone app or Rint web app. This imports workouts and
available measurements; it does not copy Fitness rings, awards, friends, or
Fitness+ media. No subscription or Strava account is required.

## Use it

1. Upgrade the Rint server (`ftcli db upgrade` includes `rint_health_04`) and
   install the updated signed iPhone app. Sign into your HTTPS server.
2. Open **Your data → Apple Health & Watch**. Choose all accessible Health
   workouts or Apple Watch only, with all history or a starting date.
3. Tap **Connect Apple Health**. Review Apple's permission sheet and Rint's
   accessible-workout count. New imports default to private.
4. Tap **Import / resume history**. Each successful read is retained in the
   phone's upload queue before its job is marked complete. Progress and failures
   persist across app restarts. Uploads resume after connectivity or login returns.
5. Enable **Automatically sync new workouts**. Rint registers Health observers
   at app launch, fetches incremental workout changes and catches up on opening.
6. Resolve **Review possible duplicates** by linking an existing activity or
   keeping a separate session. Linking preserves the original file, title,
   description, comments, likes and visibility, and retains the Health source.

**Check history again** rereads older history and detects richer data without
duplicating acknowledged workouts. **Review access and history** also rescans,
because Apple does not disclose which read permissions were granted. Missing
data may reflect permissions or the recording itself; an empty query cannot
prove that the user denied access. Adjust access in Health's app permissions.

Disconnect stops Health reads and background observers, preserving imported
activities and retained uploads. Deleting in Health does not delete a Rint
activity. Imported data is owned by the account/server used to connect. A second
account requires its own explicit connection; signing out stops observation.

## Data and calculations

Workout start/end, type, indoor/pool classification, reported active time and
distance, source identity, optional energy, routes, heart rate, cycling cadence,
running/cycling power and lap/segment events are retained where accessible.
Unknown sports use the server's **Workout** category, preserving Apple's original
activity type. Running cadence is not inferred from steps. Apple does not provide
the device's original FIT file through this interface; Rint retains its extracted
Health stream and source information as JSON.

Standalone quantity samples are read directly; quantity-series queries expand
only condensed samples into their constituent measurements. This avoids dropping
ordinary cumulative distance samples or counting a condensed sample twice.
The server merges complementary sensor/route samples at equal timestamps before
enrichment. Equally sampled newer Health revisions can correct measurements;
limited rereads preserve richer retained streams. Derived analyses produced by
the older merge are repaired from retained sources on analysis/preview access,
using `health_merge_version: 2`. Original files and sharing stay intact.
Streams keep their timestamps independently of GPS. Manual and
automatic pause/resume events carry through sensor and route samples. Modern
nonzero lap intervals and older lap-end markers use their respective timing.
Distance samples remain the distance authority; GPS supplies distance only when
sampled device distance is absent. In that case the computed distance may differ
from Health's reported total, which remains in the source export.

A total-only distance supports a summary and readable sensor charts, but no pace
chart, splits or fastest efforts. A late route/distance stream can enable those
calculations. Reported Health active time and energy are labelled separately from
Rint's elapsed/moving/pause calculations. Missing pause events cannot be recreated
from an active-time total. See [calculation methods](RINT_METRICS.md).

## Identity and recovery

Health progress is an atomic, protected file per server/account. Anchored queries
read 50 workout changes at a time; the new anchor and unfinished UUID jobs are
saved together before processing. Errors retain jobs and explanatory messages.
The outbox is also protected and atomic. Account + Health UUID + content produce
a stable delivery UUID; acknowledging an older revision cannot delete a newer
revision or another account's data. Uploads are serialized on the phone and
server; repeated background requests resolve to the same activity.
Small recoverable outbox indexes keep account/review checks from decoding every
workout repeatedly during a large history upload. Cached sport mappings allow
Health reads to resume offline for an account that has connected to its server.

Server identities use `(user, Health UUID)`, plus source bundle and Health sync
identifier/version when available. A higher sync version can replace a Health
UUID while retaining the same Rint activity. Rint recording metadata prevents a
second activity when Health and WatchConnectivity uploads arrive in either order.
Older client UUID imports are recognized. Later data enriches the activity while
retaining previously available data; changes in read access do not erase it.

Other existing activities with start times within 30 seconds, elapsed durations
within 5 seconds/2%, and distances within 10 metres/2% are candidates for user
review, across sport labels. These thresholds identify possible matches; they
are not proof of identity. Ambiguous matches are never automatically combined.
The original recording remains the authority for linked activity distance and
existing sensor coverage; Health fills missing streams and gaps over 60 seconds.
Owner-only activity JSON and full-account exports include retained Health sources.
Shared maps and analyses use the same server privacy rules as other Rint activities.

## Background limits and verification

iOS schedules background execution; "immediate" delivery does not promise an
instant server upload. Rint requests workout/route notifications, persists work
before completing callbacks, and checks the last seven days for delayed routes
or sensors. Older delayed data or expanded permissions can be recovered with
**Check history again**. A locked Health store, expired login, network loss, or
system termination can delay synchronization. No Health permission prompt is
shown from a background callback. The old global Health-enable setting is not
automatically enabled for another account; reconnect explicitly after upgrading.

Automated checks cover server identities, retries, source enrichment, exports,
privacy and duplicate decisions. Simulator tests cover account/revision outbox
isolation, persisted jobs, pause/lap conversion, sports, and offline review state.
An opt-in simulator fixture additionally uses the actual Health SDK to read
4,800 m of distance, at least 30 heart-rate and route samples. A separate native
integration check rescans the connected synthetic local demo history through the
durable upload queue and server, verifies the same activity ID/4.80 km, and
retains its private audiences and 1,500 m protection radius. These checks do not
prove personal Health history access or background sensor delivery.
Apple requires physical-device testing for background Health delivery; use the
expanded [device acceptance checklist](apple/DEVICE_TESTING.md) on the user's
iOS 27/latest-watchOS devices. Installation needs a signing team and a reachable
HTTPS server; TestFlight distribution needs the corresponding Apple access.

Primary references: Apple's [observer queries](https://developer.apple.com/documentation/healthkit/executing-observer-queries),
[anchored queries](https://developer.apple.com/documentation/healthkit/hkanchoredobjectquerydescriptor),
[read permissions](https://developer.apple.com/documentation/healthkit/authorizing-access-to-health-data),
and [workout events](https://developer.apple.com/documentation/healthkit/hkworkoutevent).
