# Physical-device acceptance gate

Need an iPhone on iOS 26+, paired Watch on watchOS 10+, Mac/Xcode signing team
and an HTTPS Rint server. TestFlight/App Store needs paid Apple Developer access.
Record models/OS, permissions, battery before/after, duration and observed results.
Simulator evidence does not satisfy these tests. Use test accounts and retain
a trusted comparison recording until this gate passes.

1. **Independent Watch:** leave the phone behind, start/run/pause/resume/lap/finish
   with display locked. Compare HR, distance, elapsed and pauses. Test indoor too.
2. **Offline:** disable network before finishing, reboot, reconnect and verify
   exactly one complete activity. Watch clears its queue only after server ACK.
3. **Recovery:** terminate/relaunch during recording. Recover HealthKit or save
   the interrupted portion. Compare route, sensors and laps. Test storage failure.
4. **Uploads:** interrupt transfers, return 500/429, expire login and retry. Check
   retained files, backoff, duplicate ACKs and UUID conflicts without overwrites.
5. **Health history:** connect with full/limited/denied read access. Preview and
   import both Watch-only and all-source histories, a date range, indoor workouts,
   and older sessions. Compare dates, sport, distance, HR/power/cadence, energy,
   pauses and laps with Health/Fitness. Repeat and verify no second activity.
   Terminate mid-import, reopen and resume; inject read errors and retry.
   Review possible Strava matches: link one, keep another separate, verify both
   sources in owner exports and unchanged titles/sharing after linking.
   Deliver Rint Watch and Health versions in each order and check one activity.
   Enable automatic sync, record in Apple's Workout app with the phone absent,
   reconnect and verify the activity appears while Rint is backgrounded and on
   foreground catch-up. Test a route arriving after the workout and run an older
   history rescan. Expand permissions, then rescan without duplicates. Sign out,
   change servers/accounts, reconnect explicitly and check account isolation.
   Disconnect and confirm observation stops. Delete in Health and confirm the
   imported Rint activity is retained.
6. **Permissions:** deny HR, route and Health-write independently. Missing fields
   remain absent. Health-save failures retain the complete Rint recording.
7. **Battery/background:** record 90 minutes and a multi-hour workout. Test calls,
   screen lock, low-power mode and system interruptions; measure gaps and drain.
8. **Privacy/social:** import, share, view as another user and anonymously, revoke
   sharing. Check protected endpoints, chart coordinates, photos, original access,
   likes/comments/mentions and block/report behavior.

Implemented, requiring physical acceptance: complete route reconstruction from
the retained draft, an independent durable Health-save queue with foreground
retry, native protected maps, interval/comparison charts, sharing controls,
community profiles, requests, inbox, comments and moderation screens.

Simulator review completed start, pause, resume, lap and finish on a paired
Ultra 3/watchOS 27. The resulting 56-sample recording remained on Watch after
relaunch. A fresh recording after the distance-anchor fix retained 89 samples and reported
52.34 s elapsed / 41.06 s active / 11.28 s paused / 37.26 s moving.
A deliberately manual fixture handoff exercised the phone outbox and
local server; it does not establish WatchConnectivity delivery. Apple explicitly
states that [file transfers are unsupported in Simulator](https://developer.apple.com/documentation/watchconnectivity/wcsession/transferfile(_:metadata:)).

The opt-in `RintSimulatorFixtures` scheme reads a synthetic Health workout through
the real SDK. Its local-server rescan test requires the named demo account at
`http://localhost:5080`, existing simulator Health onboarding, and the fixture
activity; it never runs on a physical device or against another server. It
verifies 4.80 km, preserved HR, one activity and unchanged private sharing/radius.
Run the normal `Rint` scheme for the 18 ordinary tests without fixture mutation.

Still incomplete: native push delivery. Photo attachment, profile editing
(including profile photo) and account export now have native screens and real
local transport checks. Validate selecting a photo, its preview and retry,
saving every profile field and photo, exporting a large archive, and the system
share/save sheet by touch and VoiceOver before accepting them. Simulator input routing also prevented a full iPhone scroll/drag and
tab-navigation acceptance pass; do not treat accessible button checks as proof
of touch ergonomics. See [current validation](../RINT_VALIDATION.md).

Accessible simulator actions did save the loaded profile, download its account
ZIP, open the system save/share sheet, and display the uploaded fixture photo.
Native comparison selection exposed a chart rendering defect; the corrected
solid/dashed series were visually verified in the rebuilt app. Accessible
Form/List scrolling recovered, while coordinate drag, tab-bar navigation and
system picker selection remain unverified.

The opt-in `SimulatorAccountFixtureTests` requires the same named local demo
account, unset demo birthday, Health fixture activity and a prepared account ZIP.
It preserves profile fields, reuses its synthetic photo attachment on reruns,
checks unchanged activity privacy, and streams a valid ZIP through the native
API client. It does not operate the photo picker or export share sheet.
