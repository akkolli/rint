# Rint interface redesign

## Shared web and iPhone refinement — October 16, 2026

A unified weekly overview now precedes the feed, with actual totals, last-week
context and an eight-week history. Cool neutral surfaces and consistent teal,
violet and rose measurements give the data a clearer hierarchy. Desktop uses a
wide overview and supporting library/calendar column; phone layouts reflow the
same information. Cards retain independent social and profile controls.

Optional success sounds default off, with native selection haptics and reduced-
motion-aware feedback. The appearance shortcut label now matches its action.
[Running screenshots, checks and physical-device limits](docs/rint-polish/studio-2026-10-16/README.md).


## Feed composition — October 16, 2026

Workout cards now lead with the activity instead of a large author row. One
aligned group shows distance, explicitly labelled moving/elapsed time,
corresponding pace/speed and an available supporting metric. Media stays
continuous with the card; empty route messages are omitted from the feed.
Social actions occupy one 44-pixel control row with explicit sizing. Like,
Comment and Share use the metrics' inset and column starts, with Comment spanning
the middle two columns on four-metric cards. Their matching icon/label treatment
shares the content grid instead of floating in a separate distribution.

At 390 pixels the measured card is 158.30 pixels tall, down from 250.75, while
showing four metrics instead of three. This keeps readable type and comfortable
targets. Narrow screens and accessibility text reflow the metric group. Light
and dark retain calm surfaces, subtle separators and the same hierarchy.
[Actual comparisons and checks](docs/rint-polish/feed-layout-2026-10-16/README.md).

## Copy cleanup — October 16, 2026

Removed repeated slogans, tap instructions and headings that duplicate the
selected tab. Recording setup leads with its controls; Health and export copy
are shorter. Timing definitions, privacy and recovery states remain explicit.
[Actual before/after captures](docs/rint-polish/copy-2026-10-16/README.md).

## Useful information density — October 15, 2026

The primary path now groups related information instead of stacking large,
independent panels. Feed summaries combine current mileage, previous-week
context and an actual eight-week trend. Compact media and three aligned native
metrics let the first complete workout and the next workout appear together.

Activity details place distance, active time and pace above a compact,
expandable route. Desktop places analysis beside the map. Linked chart values
retain readable plotting space; effort and split comparisons use tighter rows
with full touch targets. Records keep source, date, time and pace. The Watch
glance screen combines active/elapsed timing, distance, pace, heart rate, laps
and controls, while retaining interruption recovery and explicit completion.

At 390 × 844, main activity metrics move from y=587 to y=190 and the unchanged
220-pixel plot starts 274 pixels earlier. Browser checks caught and fixed a
units/title overlap, squeezed chart controls and unnecessarily tall split rows.
Map framing follows actual container-size changes. Light and dark use the same
layout and existing semantic colours.

[Before/after evidence and precise validation limits](docs/rint-polish/density-2026-10-15/README.md)
include the completed October 16 iPhone review. That pass corrected a vertical
effort-row separator, grouped each effort into two aligned lines, kept weekly
trends above bars and adjusted chart height/axis density for accessibility text.
Activity/record selection, system appearance and a synthetic phone recording
through recovery, synchronization, analysis and private sharing were operated.
Native changes are in simulator builds; no physical device update or test occurred.

## System appearance — October 14, 2026

Web appearance defaults to System and responds immediately to operating-system
theme changes, including when returning to a cached page. Optional Light and
Dark preferences remain available. The first paint uses the system palette;
cards, form controls, menus, charts and maps share Rint's semantic colours.
Dark map tiles are filtered independently of the route overlay so measurement
colours remain legible. Native iPhone colours already resolve from iOS traits;
the heart-rate colour now meets text contrast requirements on light panels.
Watch retains its platform-native dark appearance.

[Running browser evidence and simulator limits](docs/rint-polish/dark-2026-10-14/README.md)
document the change. Appearance edits now retain the account's other settings,
including fields that arrive after the preferences form mounts.

## Interaction and visual density — October 14, 2026

The primary path now uses position, scale, linked readouts and persistent
selection to explain workouts. Weekly bars and an actual-total line expose
changes; Records emphasize a selected achievement and compare pace across
standard distances. Source rows preserve time, pace, date and originating
workout. Route colours encode recorded measurements with a range legend, grey
missing intervals and disconnected privacy breaks.

Charts accept direct taps without a slider or inspection mode. Workout cards
use generous activity hit areas with an explicit avatar/profile target. Empty
sections and repeated actions are reduced, and native sharing presents audience,
route protection and free exports without a repeated introductory panel.
The running review caught and fixed oversized web icons, desktop overflow,
missing route-to-chart events and plot lines extending beyond a selected domain.

[Actual before/after screenshots and validation limits](docs/rint-polish/interaction-2026-10-14/README.md)
document this simulator/browser round. It preserves the existing recording,
Health/import, synchronization and privacy architecture.


## Product structure reset — October 11, 2026

The user’s concern was about the entire experience: Rint still felt like a
settings dashboard with new styling. This section supersedes the earlier
navigation and account-layout descriptions below. It is an implementation and
verification record, not a claim that Rint has reached Strava or Apple Fitness
quality across every surface.

### Design direction

A calm, athletic interface with a clear order: the effort first, the supporting
context second, and configuration only when needed. Warm white, deep forest,
lime actions and consistent sensor colours remain Rint’s identity. Stronger
numeric typography, fewer repeated headlines and restrained separators give
workouts more prominence than containers. No invented activity, stock social
content or decorative performance charts were added.

- **One navigation structure:** Feed, Progress, Add/Record, People and You.
  Desktop web uses a persistent rail; phone web uses a bottom bar. Activity
  history, the map and import tools remain directly accessible. Appearance,
  language, logout and administrative controls are retained.
- **A real athlete home:** `/profile` now presents identity, relationships,
  recent activities and entry points to the library and data tools. Settings
  have their own heading and section navigation. The native You tab opens the
  athlete profile with imports and preferences as destinations.
- **A useful feed:** account-scoped monthly totals come from the history API,
  independent of the paginated feed. Desktop adds six months of distance and a
  training calendar. Phone prioritizes a compact monthly summary and activities.
  Photo cards use the photo as their main media instead of stacking a route
  above it. Missing routes get a small, honest note.
- **Stable interactions:** the API exposes route-presence metadata under map
  permissions so web and native feed cards reserve their preview space before
  loading. This fixes a reproduced case where an asynchronous preview shifted
  the intended workout link under a click. Failed web pagination keeps existing
  activities and retries the same page; failed first loads no longer leave
  permanent skeletons.
- **Workout details:** remove the repeated introductory section, keep sharing
  immediately available, and bring the complete metrics and chart into the
  initial 390×844 viewport. Additional Health-reported totals stay in calculation
  details. The chart initially selects a real sample rather than an empty time.
  Original recordings, photos, social controls and exports remain available.
- **Clearer entry:** Add activity exposes Health and Strava, plus upload/manual
  entry. File limits and optional photos, notes and equipment are disclosed
  progressively. Privacy stays visible. Radio choices now have an actual group
  and do not toggle modes when clicking the already-selected choice. Custom sport
  names fall back to readable names when upstream translations are missing.
- **Training:** annual totals have a clear numeric hierarchy; all twelve months
  fit the small phone chart instead of hiding recent months offscreen.

### Evidence and limits

Actual screenshots below are from the running local product and synthetic demo
account. Numbers come from its stored workouts. Different before/after views
show the same account and activity. Screenshots are unaltered browser captures.
After the Mac unlocked, the native app received the running-interface review
recorded below. Earlier simulator screenshots further down remain historical
evidence; physical-device acceptance is still deferred.

| Profile before | Profile after |
| --- | --- |
| ![Old settings-first profile](docs/rint-polish/product-2026-10-11/profile-before.jpg) | ![Athlete home](docs/rint-polish/product-2026-10-11/profile-desktop-after.jpg) |

| Workout before, 390 px | Workout after, 390 px |
| --- | --- |
| ![Chart below the fold](docs/rint-polish/product-2026-10-11/activity-phone-before.jpg) | ![Metrics and chart visible](docs/rint-polish/product-2026-10-11/activity-phone-after.jpg) |

| Feed | Entry | Training, 320 px dark |
| --- | --- | --- |
| ![Phone feed](docs/rint-polish/product-2026-10-11/feed-phone-after.jpg) | ![Activity entry](docs/rint-polish/product-2026-10-11/add-phone-after.jpg) | ![Training chart](docs/rint-polish/product-2026-10-11/progress-dark-320.jpg) |

Remaining acceptance work: comprehensive native accessibility and error-state
review, Dynamic Type and VoiceOver on-device, touch scrubbing on physical hardware,
Watch/phone background recovery and transfer, and slow-network performance.
Existing limitations (native push delivery, distribution/signing, large web
bundle, and upstream settings still needing further refinement) are not closed
by this redesign. Free metrics/exports, privacy enforcement, AGPL and self-hosting
remain requirements.

### Native refinements after unlocking

The simulator exposed issues that a build could not: an empty route panel pushed
social actions offscreen, import choices followed maintenance status, unavailable
chart choices occupied the sensor selector, and Comment landed at the top of a
long activity page. These were corrected in the running product. Sharing is now
available in the activity navigation bar and owner feed action; privacy is reviewed
before opening the system share sheet. Comparison follows the primary chart.

Health onboarding now prioritizes selection and import, followed by automatic sync.
Changing the selected history requires a fresh review before import, preventing the
old filters from being used silently. Annual training includes all twelve months
in one view. The iPhone tab bar remains on primary destinations and steps aside
for focused activity and Health screens.

| Native feed before review | Native feed after correction |
| --- | --- |
| ![Empty route reserved too much space](docs/rint-polish/product-2026-10-11/native-feed-before-review.png) | ![Compact workout and accessible actions](docs/rint-polish/product-2026-10-11/native-feed-after.png) |

| Data screen before | Data screen after |
| --- | --- |
| ![Maintenance ahead of imports](docs/rint-polish/product-2026-10-11/native-imports-before-review.png) | ![Health and Strava first](docs/rint-polish/product-2026-10-11/native-imports-after.png) |

| Native chart interaction | Direct conversation entry | Training year |
| --- | --- | --- |
| ![Actual heart-rate scrubbing](docs/rint-polish/product-2026-10-11/native-chart-scrub-after.png) | ![Comment opens the conversation](docs/rint-polish/product-2026-10-11/native-comment-entry-after.png) | ![All twelve months](docs/rint-polish/product-2026-10-11/native-progress-after.png) |

| Health onboarding | Newly imported workout |
| --- | --- |
| ![History selection and clear sync state](docs/rint-polish/product-2026-10-11/native-health-after.png) | ![Sensor chart from the Health rescan](docs/rint-polish/product-2026-10-11/native-new-health-chart-after.png) |

A Health rescan imported one previously unimported simulator workout, then a
second rescan added none. Counts therefore differ in screenshots taken after that
workflow. The original Health activity kept its private audiences and endpoint
protection. The full evidence and limitations are in `RINT_VALIDATION.md`.

This increment polishes the path from importing a workout, through the feed and
activity charts, to setting its audience and sharing its link. It also establishes
the same visual direction for native iPhone recording, Health onboarding and
Watch recording. It is an implementation and visual review, not a physical-device
or daily-use acceptance sign-off.

## What the running interfaces showed

The old web home placed navigation modes, a promotional block and four boxed
statistics above the feed. Workout cards used small icons in place of metric
labels. Activity details devoted the first phone screen to an empty map, followed
by a dense list of equally weighted values. A fixed footer covered content.
The native sign-in used a standard form with little distinction between the
product introduction and the connection task. These are visible in the actual
captures below.

## One direction: your space to move

The design uses warm neutral backgrounds, charcoal typography, lime for primary
actions, violet for routes and pace, rose for heart rate, and amber for power.
Dark appearance uses corresponding readable colours. A small `r.` mark gives
Rint an identity without borrowing another product's branding or assets.

System fonts keep the web close to iOS and avoid another font download. Large
headings establish the purpose of a screen; named metrics and proportional units
make workout values easy to scan. Monospaced digits keep recording clocks and
chart readings stable. Spacing follows a small repeated scale instead of giving
every element the same panel and importance.

The feed is the primary home content. The desktop puts history and training views
in a quieter side column. On phones, persistent navigation keeps Feed, Progress,
Add, People and Your data within reach. Native iOS uses its own tab/navigation patterns
and SF Symbols; the web uses a consistent small stroke-icon set.

Activity cards lead with the athlete, time, title and named metrics. Real route
outlines and protected photos provide the visual content. Indoor and private
routes get an honest alternative state. Outlines are explicitly labelled; they
do not imply the presence of map tiles.

Activity details lead with distance, moving time, pace and heart rate. Elapsed and
paused time sit underneath. Charts are the next dominant element; advanced
interval, comparison, route and calculation controls expand when needed. Splits,
device laps and best efforts share a clear selector. Administrative controls and
the original recording remain available in a separate disclosure.

Sharing opens audience, route protection and free export controls. Web and native
screens load the actual persisted activity audience, route audience and endpoint
radius before allowing a save. Native sharing now offers the same explicit
audiences and radius controls. Omitting a field cannot reset another setting.

Recording gives the elapsed clock and current values visual priority, followed
by a dominant Pause/Resume button. Lap and Finish are distinct secondary actions;
Finish requires a deliberate choice. Watch recording separates its glanceable
metrics from a second controls page. Retained workouts and recovery/sync messages
stay connected to the existing recorder and outbox.

Health onboarding starts with a clear explanation, history range and Watch-only
selection, then access, progress and automatic sync. A possible duplicate requires
selecting a candidate or a separate workout before confirming. Permissions and
private import defaults remain explicit.

## Functionality and performance

Existing import, recording, Health synchronization, likes, comments, visibility,
moderation, editing and export APIs are reused. No subscription checks or license
changes were added. Legacy web recordings retain their existing detail controls.

A new access-controlled route-preview endpoint sends at most 512 GPS points plus
31 gap markers per visible feed card. Privacy redaction runs before simplification.
It excludes sensor streams and preserves disconnected route sections. There is
no persistent route cache. This prevents every card from downloading the full
workout stream; calculations still use the complete recording.

Native verification also found and fixed the sports response envelope mismatch
that prevented a successful login from loading its feed. Timeline decoding now
accepts restricted/null metrics and displays both FitTrackee RFC 1123 dates and
ISO 8601 dates. Regression tests cover those responses.

Charts retain existing sampling-gap and peak-preservation logic. Native tap/drag
selection persists after release, and an accessible time slider offers another
way to inspect a reading. Web charts retain touch scrubbing, accessible sliders,
selection zoom, interval analysis and comparison. Reduced motion and visible
keyboard focus are supported; primary controls and native social/duplicate
choices have comfortable touch targets. Full VoiceOver and Dynamic Type audits
remain to be performed.

## Actual before and after

These are unaltered captures of the running local app with synthetic activities.
Phone web review used 390 × 844. Desktop after review used 1365 × 900;
the desktop before capture used the original 1275 × 717 window. The native
captures include the iPhone 17/iOS 27 simulator frame. This initial set includes
only a native sign-in before capture; the expanded review below also captures
the preceding Rint feed before its next redesign.

| Phone feed before | Phone feed after |
| --- | --- |
| ![Original phone feed](docs/rint-design/rint-feed-before-phone.jpg) | ![Redesigned phone feed](docs/rint-design/rint-feed-after-phone.jpg) |

| Activity before | Activity after |
| --- | --- |
| ![Original activity](docs/rint-design/rint-activity-before-phone.jpg) | ![Redesigned activity](docs/rint-design/rint-activity-after-phone.jpg) |

| Desktop before | Desktop after |
| --- | --- |
| ![Original desktop](docs/rint-design/rint-feed-before-desktop.jpg) | ![Redesigned desktop](docs/rint-design/rint-feed-after-desktop.jpg) |

| Native sign-in before | Native sign-in after |
| --- | --- |
| ![Original native sign-in](docs/rint-design/rint-native-before.png) | ![Redesigned native sign-in](docs/rint-design/rint-native-login-after.png) |

## Verified complete web path

A fresh synthetic Strava ZIP contained a 15-minute loop with GPS, heart rate,
cadence and elevation. Review defaulted to private; processing imported one
activity with no errors. It appeared in the chronological feed with 2.67 km,
15:00 and 142 bpm. Heart-rate scrubbing selected 131 bpm at 08:10. Splits and
best efforts were available. Follower sharing saved successfully while route
visibility stayed private, and copying the link explained that privacy still
applies. At that stage the local demo account had no followers.

A repeat archive returned three duplicates with no new activities. A free CSV
export contained 361 sample rows. A like, its undo, and a private comment were
saved through the UI. No real fitness history was uploaded or shared.

| Import completed | Imported feed |
| --- | --- |
| ![Import completed](docs/rint-design/rint-import-complete-after-phone.jpg) | ![Imported workout in feed](docs/rint-design/rint-imported-feed-after-phone.jpg) |

| Chart selection | Protected sharing |
| --- | --- |
| ![Imported heart-rate reading](docs/rint-design/rint-imported-chart-after-phone.jpg) | ![Follower sharing with private route](docs/rint-design/rint-imported-sharing-after-phone.jpg) |

## Initial native review and remaining checks

The locally signed iOS 27 simulator build was inspected for sign-in, the live
feed, routes, activity metrics, chart selection, Health setup and history-date
selection, and recording setup. A persistent native heart-rate tap displayed
152 bpm at 19:25. The Watch Series 11/watchOS 27 ready screen was inspected;
active Watch recording was not tested.

| Native feed | Native chart |
| --- | --- |
| ![Native feed](docs/rint-design/rint-native-feed-after.png) | ![Native selected chart sample](docs/rint-design/rint-native-chart-after.png) |

| Health setup | Recording setup |
| --- | --- |
| ![Health onboarding](docs/rint-design/rint-native-health-after.png) | ![Recording setup](docs/rint-design/rint-native-record-after.png) |

![Watch ready screen](docs/rint-design/rint-watch-after.png)

The initial redesign passed 35 Rint Python checks, 407 Vue tests and 13 native tests.
Web production build, type checking and lint pass. Native iPhone and embedded
Watch targets compile. Web checks at 320 × 740 found no horizontal page overflow;
split tables scroll within their own container. Light/dark charts were inspected.

Physical devices are still required for recording/paused/recovery acceptance,
Health permissions and actual history, watch-to-phone transfer, offline/background
recovery, battery behaviour, and native scroll/drag ergonomics. Simulator taps,
compilation and conversion tests do not establish these. An Apple signing team
and reachable HTTPS server are still needed for that stage.

The next increment below extends the layout work and implements native
interval/comparison, map privacy, community/moderation and inbox tools. The web
bundle is smaller but retains its size warning; no web UI dependencies were added.
See [RINT_VALIDATION.md](RINT_VALIDATION.md) and
[DEVICE_TESTING.md](apple/DEVICE_TESTING.md) for release gates.

## Expanded design and UX increment

The next running-interface review exposed oversized native feed introductions,
generic profile/account panels, a crowded Watch sport picker, unlabelled native
audience menus and asynchronous social states that refreshed too early.

The feed now starts with a compact heading and workout cards. Five destinations
match across phone web and iPhone: Feed, Progress, Add/Record, People and Your data.
Profiles lead with identity, bio/location and clear community counts. Account
navigation uses a quieter desktop sidebar and one accessible selector on phones;
the account body no longer sits in a large empty panel. Notifications have a
distinct purpose, pending controls, real loading and retry states. New-page web
navigation starts at the top, and back navigation restores its position.

Progress supports year/sport selection, zero-value months, month drilldown and
sport-specific personal bests. Earlier FitTrackee originals can be analyzed in
resumable batches. Native maps display the server-protected route, with an
outline option; interval/comparison controls reuse the same analysis API.
The native community includes searchable profiles, follow requests, invitations,
blocking/reporting and an in-app inbox. Native photos have a gallery and zoom.

The Watch ready screen uses a separate sport-selection screen so Start is visible.
Its recording page uses stable digits, clear units and a dominant Pause/Resume;
lap and Finish remain on the controls page. Sensor callbacks retain independent
timestamps and add distance anchors only when distance is measured or a pause
boundary occurs. This avoids treating unchanged values on every HR callback as
evidence that the athlete stopped. Health-save recovery also uses independent
distance anchors, preserving totals when other sensor samples fall between them.

### Actual captures from this increment

These are unchanged screenshots of the running app, with synthetic accounts.
Native before means the preceding Rint redesign, not the original FitTrackee UI.
Desktop profile captures use 1365 × 900; phone web captures use 390 × 844.

| Native feed before | Native feed after |
| --- | --- |
| ![Previous native feed](docs/rint-polish/native-feed-before.png) | ![Compact native feed](docs/rint-polish/native-feed-after.png) |

| Desktop profile before | Desktop profile after |
| --- | --- |
| ![Generic profile](docs/rint-polish/web-profile-before.jpg) | ![Profile and account hierarchy](docs/rint-polish/web-profile-desktop.jpg) |

| Community on phone | Saved native privacy |
| --- | --- |
| ![People directory](docs/rint-polish/web-people-phone.jpg) | ![Labelled native sharing](docs/rint-polish/native-sharing-after.png) |

| Watch ready | Watch recording |
| --- | --- |
| ![Compact Watch setup](docs/rint-polish/watch-ready-after.png) | ![Active Watch workout](docs/rint-polish/watch-recording.png) |

| Phone web feed | Free phone charts |
| --- | --- |
| ![Compact phone feed](docs/rint-polish/web-feed-phone.jpg) | ![Health heart-rate chart](docs/rint-polish/web-health-chart-phone.jpg) |

| Native profile save | Native account export |
| --- | --- |
| ![Profile saved](docs/rint-polish/native-profile-saved.png) | ![Downloaded full account archive](docs/rint-polish/native-account-export.png) |

| Native comparison before | Native comparison after |
| --- | --- |
| ![Incorrect connecting line](docs/rint-polish/native-comparison-before.png) | ![Independent solid and dashed series](docs/rint-polish/native-comparison-after.png) |

![Native imported Health metrics](docs/rint-polish/native-health-activity-after.png)

The Health SDK/local-server rescan verified 4.80 km, retained HR, unchanged
private sharing/radius and one activity. Watch start/pause/resume/lap/finish were
exercised. WatchConnectivity file transfer is unsupported in Simulator; phone
upload of the recorded file was tested using a labelled manual fixture handoff.

Current automated counts and limitations are in [RINT_VALIDATION.md](RINT_VALIDATION.md).
Remaining gaps include physical reliability, full native touch/VoiceOver/Dynamic
Type and photo-picker acceptance, push delivery, large exports, production deployment and further initial-load work.
The acceptance standard has not been lowered to successful compilation.

Design references: [Strava](https://www.strava.com/) and
[Apple Fitness](https://apps.apple.com/us/app/apple-fitness/id1208224953).
Native chart interaction follows Apple's
[ChartProxy documentation](https://developer.apple.com/documentation/charts/chartproxy).

Native account forms now support editing profile fields/photo and requesting,
checking and downloading a full data archive. Activity photos have a selection
preview, metadata removal and explicit retry. The running iPhone simulator saved
the loaded profile, downloaded a 1.5 MB account ZIP, opened its system save/share
sheet and displayed the uploaded fixture in the native photo gallery. Web photo
viewing also opened from the Space key. Full picker/touch acceptance remains open:
the system photo and Files pickers opened, but exposed no actionable accessibility
controls and coordinate input failed. The Watch
sport list places the current sport first and returns directly to recording
setup after choosing it. The Finish confirmation explicitly dismisses when
saving starts.

The actual native comparison review found a false line connecting two workouts.
Distinct String section identifiers and explicit workout colour grouping now keep
the violet current workout and dashed amber comparison separate. The corrected
chart was rebuilt and visually verified using the same two activities. Comparison
loading, missing samples and retry stay beside the chart. Changing interval bounds
clears old results, and responses for superseded selections are ignored. The default
whole-workout interval calculation was exercised; native slider/drag acceptance
remains open.

| Native photo gallery | iOS archive save/share |
| --- | --- |
| ![Uploaded synthetic photo](docs/rint-polish/native-photo-gallery.png) | ![System ZIP sheet](docs/rint-polish/native-account-share-sheet.png) |
# October 14 — training, activity details and recording

The central tasks now have distinct layouts: Week answers how much the user
trained, Records answers what their best efforts are, and History finds the
workout. The feed promotes weekly distance instead of an annual summary.
Record cards lead with time and distance, retain their source/date, and open the
exact interval. Returning preserves the selected section.

Activity details lead with a geographic route and a compact metric grid, then
separate charts, best efforts and splits/laps. Sensor-only samples do not break
maps, while redacted locations do. Thirty-second pace avoids an unreadable
scale; the full range remains available. Sharing combines the workout story,
photos, audience and protected preview before opening the native share sheet.

Watch controls have an explicit entry and fit pause/resume, lap and finish on
one screen. Saved summaries distinguish device retention, phone receipt and
server acknowledgement. The paused clock and distance are checkpointed; fresh
simulator checks include app termination and relaunch.

The existing forest/lime identity extends to the native and browser icons.
These changes preserve free metrics/exports and the existing open-source
license. [Actual screenshots and verification boundaries](docs/rint-polish/2026-10-14/README.md)
include the previous training layout and the new Week/Records screens.
