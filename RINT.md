# Rint — your fitness, your data

An AGPL-3.0-only FitTrackee fork with free metrics and native Apple clients.
This is a working incremental release for evaluation. Physical-device recording,
recovery and battery validation are required before daily use.

## Try it

After starting the server, open <http://localhost:5080> and register.
For local development only, `scripts/rint-demo.py` can create a synthetic QA
account; its credentials stay in the ignored `.local/demo.json` file. Demo activities are clearly labeled. Select **Bring your
Strava history**, upload an account export, review sport mappings and visibility,
import/resume, and open an activity. Inspect charts, select intervals, review laps
and sustained efforts, export data, then save sharing settings. Routes default to
private. **Your progress** includes full-account monthly totals and bests by sport.

Web feed cards expose likes, comments and sharing. Existing FitTrackee follows,
mentions, profiles, invitations, notifications, block/report and moderation APIs
remain in use. Native clients include feed, likes/comments, recording, charts,
history, protected route maps, interval/comparison charts, people/profiles,
follow requests, inbox, invitations, moderation and unit/privacy preferences.
Native photo attachment (with metadata removal), profile editing and full-account
export/status/download screens are implemented and have local transport checks.
The simulator also verified saving a profile, downloading an archive, opening
the iOS save/share sheet and viewing an attached photo. Complete touch/picker
acceptance remains open.
No metric, chart or export requires a subscription.

## Self-host

Requires Docker and Compose 2.30+. The PostGIS image targets Linux amd64; ARM
hosts may need emulation or a locally built PostGIS image. Docker is unavailable
in this development environment, so the image build and deployment smoke test
remain unverified.

```sh
python3 scripts/rint-configure.py
docker compose --env-file .env.rint -f compose.rint.yml up --build -d
docker compose --env-file .env.rint -f compose.rint.yml logs -f web worker
```

This builds this fork, migrates the database and starts web, PostGIS, Redis and
the export/email worker. Open <http://localhost:5080> and register. Use FitTrackee's
`ftcli users` commands to grant the first account admin access, then configure
registration in administration. SMTP settings `EMAIL_URL`/`SENDER_EMAIL` enable
confirmation, invitations and email notifications; SMTP is optional locally.

For phone access, use an HTTPS reverse proxy and your domain. Set `UI_URL` to its
HTTPS address and `RINT_SOURCE_URL` to your published fork/revision before
building; this adds the corresponding source link to About. Allow 512 MB request bodies and a 180-second timeout. The web port
binds to localhost. Keep your original migration ZIP. Back up database and uploads
together, keep `.env.rint` privately, and test restoration before upgrades.
`down` preserves volumes; `down -v` permanently removes server data.

## Local macOS development

Requires Python 3.13, Node 22+, PostgreSQL 17/PostGIS, Redis and libmagic.
Development services use ports 55432/56379, storing data in `.local` without
enabling system startup services.

```sh
uv venv --python 3.13
uv pip install -e . pytest ruff mypy time-machine pytest-xdist
npm --prefix fittrackee_client ci
sh scripts/rint-dev-services.sh
source .local/env
.venv/bin/ftcli db upgrade
npm --prefix fittrackee_client run build
.venv/bin/flask --app fittrackee --debug run --host 127.0.0.1 --port 5080
```

Optional UI fixtures: `.venv/bin/python scripts/rint-demo.py` after sourcing the
environment. It refuses production/other databases. Stop isolated services using
PostgreSQL's `pg_ctl -D .local/postgres stop` and `redis-cli -p 56379 shutdown`.

## iPhone and Apple Watch

### Private HTTPS on a Mac

For a first device installation, an existing Tailscale network can provide a
trusted HTTPS address without opening the server to the public internet.
Use the Mac's full `*.ts.net` hostname. Enable Serve/HTTPS in Tailscale's admin
page, and connect the iPhone to the same Tailscale network.

```sh
.venv/bin/python scripts/rint-mac-server.py prepare --url https://YOUR-MAC.YOUR-TAILNET.ts.net
.venv/bin/python scripts/rint-mac-server.py install
/Applications/Tailscale.app/Contents/MacOS/tailscale serve --bg --https=443 http://127.0.0.1:5081
```

This setup uses production mode, a separate `rint_personal` database, Redis
database 1, private uploads under `.local/personal`, and a supervised web server
and export worker. The demo at port 5080 remains separate. Secrets are stored in
`.local/personal/environment.json`, excluded from Git. The login service is
`~/Library/LaunchAgents/org.rint.personal-server.plist`; logs are in
`.local/personal/server.log`. The Mac must be awake, logged in, online, and
connected to Tailscale. Startup after a full Mac reboot has not been verified.

Register your personal account through the HTTPS web interface. Email is not
configured in this setup, so activate your chosen account locally:

```sh
.venv/bin/python scripts/rint-mac-server.py cli users update YOUR_USERNAME --set-role owner
```

The first registration fills the one-account limit. An owner can deliberately
raise that limit in administration to invite other people. Keep the account
password in your password manager. Back up `rint_personal` with PostgreSQL's
`pg_dump` and retain `.local/personal/uploads` and the private environment file
together; pause the Rint service while taking a consistent backup. Backups on
this same Mac do not protect against losing the Mac.

The iPhone must have Developer Mode enabled. Sign in to an Apple development
team in Xcode so it can provision **HealthKit** for both Rint and RintWatch.
Enable Developer Mode on the paired Watch as well, and pair both devices with
the Mac. In Xcode 27, use Device Hub → Add Device → Pair Nearby Device. Build
for the actual Watch first so its UDID is registered in the development profile;
a phone-only build can produce a Watch profile that excludes the Watch.
A device build can prefill the server address without hard-coding a private
hostname in the source:

```sh
DEVELOPER_DIR=/Applications/Xcode-beta.app/Contents/Developer xcodebuild \
  -project apple/Rint.xcodeproj -scheme RintWatch -configuration Release \
  -destination 'id=YOUR_WATCH_UDID' -derivedDataPath apple/.device-build \
  DEVELOPMENT_TEAM=YOUR_TEAM_ID \
  -allowProvisioningUpdates -allowProvisioningDeviceRegistration clean build
DEVELOPER_DIR=/Applications/Xcode-beta.app/Contents/Developer xcodebuild \
  -project apple/Rint.xcodeproj -scheme Rint -configuration Release \
  -destination 'id=YOUR_PHONE_UDID' -derivedDataPath apple/.device-build \
  DEVELOPMENT_TEAM=YOUR_TEAM_ID RINT_DEFAULT_SERVER_URL=https://YOUR-MAC.YOUR-TAILNET.ts.net \
  -allowProvisioningUpdates -allowProvisioningDeviceRegistration build
.venv/bin/python scripts/rint-check-apple-bundle.py \
  apple/.device-build/Build/Products/Release-iphoneos/Rint.app \
  --phone-udid YOUR_PHONE_UDID --watch-udid YOUR_WATCH_UDID
```

The packaging check validates the actual built phone and Watch bundles, including
matching version/build numbers, the companion identifier, and Health usage
descriptions. The optional device arguments also check that the signed profiles
include the target devices. These checks complement signature verification and
device testing.

Install the signed `apple/.device-build/Build/Products/Release-iphoneos/Rint.app`
on the chosen iPhone through Xcode or `xcrun devicectl device install app`.
The companion is embedded; install it through the iPhone Watch app or Xcode's
paired Watch destination, then launch both apps. Watch recordings synchronize
through the phone when they reconnect; this private setup does not provide
direct internet access from a standalone cellular Watch. A successful build or
installation does not complete the physical checks in `apple/DEVICE_TESTING.md`.

iPhone recording uses APIs introduced in iOS 26; targets are iOS 26/watchOS 10.
An older-iOS fallback is future work. Install Xcode with the corresponding SDK
and XcodeGen:

```sh
cd apple
xcodegen generate
open Rint.xcodeproj
```

Select your development team for both apps and tests. Change bundle identifiers
if needed, keeping the watch companion identifier in `project.yml` consistent.
Enable HealthKit for both signed apps. Sign into your HTTPS server on the phone,
choose a sport, and authorize Health/location when recording or importing.
The watch receives account identity and sport configuration from the phone.
It then records without a nearby phone, retaining workouts until server ACK.

Device recordings checkpoint to disk. The phone uses background uploads, network
restoration, persistent retry backoff and best-effort system background tasks.
Stable UUIDs prevent duplicate delivery. In **Your data → Apple Health & Watch**,
review access, choose all Health or Watch-only history and an optional start date,
then import/resume. Enable automatic sync for new workouts. Progress and read
failures survive restarts. New imports are private; readable sensor data appears
in the free native and web charts. Possible matches with existing activities
require review. Rint-created Health workouts link to the original recording even
when Health and Watch uploads arrive in either order. Credentials live in Keychain.
Expired logins require reauthentication; queued workouts remain retained and tied
to their original server/account.

A signed development build has been installed and launched on the user's
physical iPhone and Apple Watch; see
`RINT_VALIDATION.md` for the current installation and test status. TestFlight and
App Store distribution have not been configured. Physical installation alone
does not establish workout reliability.
Health writes can fail independently of server uploads; their own protected
queue retains the job until workout/route persistence succeeds. Foreground retry
can reconstruct the complete route from the retained draft without duplicating
the Health workout. Physical recovery and battery acceptance remain open.
The OS controls background retry timing. Native push notifications and live
session mirroring remain future work. Native photo/profile/export workflows
compile and pass local transport checks; simulator profile save, archive download,
system save/share presentation and gallery viewing were also exercised. Picker
and complete touch acceptance are still required. Simulator Watch file transfers are unsupported; the validated
phone upload used a clearly labelled manual synthetic handoff.

See [Apple Health import and sync](RINT_HEALTH.md) for permissions, retained data,
duplicate rules, background timing, and device validation.

## Validation

See [architecture/upstream alignment](RINT_ARCHITECTURE.md),
[calculation methods](RINT_METRICS.md), [validation results](RINT_VALIDATION.md)
and [device testing](apple/DEVICE_TESTING.md).
Automated tests use real PostGIS for import/resume/deduplication, privacy, indoor
streams, history, social interaction and exports. Numerical tests include real
FIT fixtures. Native disk/encoding tests run on an iPhone simulator; both app
targets compile with local simulator signing. An opt-in synthetic Health SDK
reader test and a native Health-to-local-server rescan check also pass; these
are separate from physical-device evidence.

```sh
source .local/env
RINT_INTEGRATION=1 .venv/bin/pytest tests_rint -q
.venv/bin/ruff check rint_core fittrackee/rint tests_rint
.venv/bin/mypy rint_core fittrackee/rint --follow-imports=silent
npm --prefix fittrackee_client run build
cd apple
xcodebuild -project Rint.xcodeproj -scheme Rint -destination \
  'platform=iOS Simulator,name=iPhone 17' CODE_SIGN_IDENTITY=- CODE_SIGNING_ALLOWED=YES test
```

The simulator command uses local ad hoc signing so Keychain storage works.
It does not select an Apple development team or sign for physical devices.

Next release: physical reliability testing, large real export validation,
background migration jobs, native touch/photo-picker acceptance, push
notifications and multisport support. The current validation report records
remaining input-tool and deployment limitations explicitly.
