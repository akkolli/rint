# Web and iPhone visual refinement — October 16, 2026

The shared palette now uses cool neutral surfaces, teal distance, violet pace,
rose heart rate, and lime actions. The home screen leads with a single weekly
training overview: real distance, comparison with last week, activity count,
recorded hours, and an eight-week bar history. On desktop this spans the content
area above the feed and library/calendar column. Phone layouts reflow the same
information. Existing routes, photos, precise timing, privacy and social actions
remain connected to the existing data and navigation.

Workout cards have clearer numeric hierarchy, separated units, consistent
insets, and color-coded measurements. Desktop navigation has a restrained active
marker. The web appearance shortcut now actually switches to the appearance
named by its label; System remains available in preferences.

Likes have restrained visual feedback on web and selection haptics on iPhone.
Optional quiet two-note confirmation sounds are off by default: enable them in
the web account menu or iPhone Units & privacy > Interaction. Preferences are
local to the browser/device. Audio only follows a successful like, never failure
or undo. Native system sound playback respects the silent switch. Web feedback
failure cannot interrupt the action. Motion respects reduced-motion preferences.

## Verification

- Production web build and TypeScript checks passed; both lint checks passed.
- Full web suite initially passed 428/430 tests; two summary-text expectations
  were updated for the redesigned labels. The affected snapshot/card tests then
  passed (7/7); after the appearance and mobile fixes, the combined theme,
  snapshot and card run passed (11/11). The final contrast-only build passed.
- Native simulator build passed with its Watch companion. Native appearance and
  training tests passed (9/9). Contrast testing caught muted text below 4.5:1 on
  the soft light surface; this was corrected on both platforms. The native
  contrast test now also covers the new distance color.
- Browser reviewed at 320, 390 and 1280 pixels, in dark and light. No page
  overflow at tested widths; all four metric values and units occupy one line
  at 390 pixels. Like/undo and the weekly date-filtered activity link were
  operated. Sound preference was toggled and restored to off.
- Actual iPhone simulator light appearance reviewed; Like/undo operated without
  navigating away from the feed. Simulator signing was corrected to retain
  normal keychain access. No physical iPhone or Watch was installed or tested.
- Native dark and enlarged-text visual checks were not completed: simulator
  display test menu controls were disabled. Both palettes pass automated
  contrast checks; accessibility sizes use a stacked overview and metric layout.
  Audio loudness and haptic feel require physical-device verification.
- The existing local demo and private web processes were refreshed to load the
  final assets. No database schema, sharing permissions or recording logic changed.

## Captures

[Desktop dark](web-desktop-dark.jpg) · [Phone web dark](web-mobile-dark.jpg) ·
[Phone web light](web-mobile-light.jpg) · [320-pixel web](web-320-dark.jpg) ·
[Actual iPhone simulator](iphone-overview.png)

Captures are unaltered screenshots of the running application with the existing
synthetic demo account. The iPhone image includes the simulator frame.
