# Reproducible calculations — method 1.0.0

Original recordings and metadata remain separate from normalized/calculated data.
JSON exports include both; CSV exports contain normalized samples. Reproduce
results by running `rint_core.analyze(recording)` with this method version.

### Route colour display

Route colours are a display layer over the retained GPS and sensor streams;
they do not change splits, sustained efforts or exported originals. Power is
preferred, then explicitly labelled heart rate or pace when power is absent.
Five bands divide the recorded activity's minimum-to-maximum range, shown in
the legend. They are relative to that workout, not physiological zones or an
absolute comparison between workouts.

Each displayed route edge uses the nearest valid sensor reading at its midpoint
time, with a maximum offset of 15 seconds. Missing readings render grey. Existing
sensor gaps and route/privacy breaks are not bridged. For display performance,
each route segment keeps at most approximately 500 GPS vertices, including its
endpoints. Inspection uses timestamps to connect the route marker to chart
readouts; pace retains the documented 30-second display window. Original samples
and calculation method 1.0.0 remain unchanged.

* Streams use elapsed seconds `t`, cumulative metres `d`, GPS degrees, bpm, watts
  and elevation metres. Cadence retains device counts/minute; some running devices
  report cycles, others steps. Conversion from sport alone is unsafe. Zero stays
  zero; missing data stays absent. Timed sensors need no GPS. Duplicate timestamps
  merge fields and sort by time. Limits: 250,000 samples, seven days, 20,000 km.
* Device distance is authoritative. Resets continue from the accumulated value;
  intervening sensor samples interpolate distance. GPS is a fallback using Earth
  radius 6,371,008.8 m. Reject jumps above 30 m/s and drift below 0.3 m/s. GPS gaps
  over 60 seconds gain no distance; device gaps keep totals but block best efforts.
* Elapsed is last minus first observed timestamp. Explicit state determines
  pauses. Active time includes indoor recording without distance. Moving time
  counts observed active distance-increasing intervals with gaps <=60 seconds.
  This documented policy does not reproduce Strava's proprietary moving time.
* Crossings interpolate linearly. Splits use 1,000 m or 1,609.344 m and label final
  partials. Pace includes elapsed time and pauses. Device laps and selected
  intervals use the same method.
* Sustained efforts cover 400 m, 1 km, 1 mile, 5 km, 10 km, 21,097.5 m and 42,195 m.
  Evaluate distance vertices and vertices shifted by effort distance to find the
  minimum elapsed time in the linear model. Keep pauses; exclude gaps >60 seconds.
  GPS precision still limits the accuracy of any result.
* Sensor averages integrate trapezoids on each sensor's independent timeline,
  never bridging gaps >60 seconds. Every average includes coverage seconds.
  GPS-only samples cannot reset sensor continuity.
* CSV-only activities keep totals without sampled splits or verified bests.
  Repeated Strava Distance headings use the later precise metres field; simplified
  single-Distance CSVs use kilometres. This interpretation stays in metadata.
  Original recordings take precedence over CSV totals.
* Bests group by sport and index imported/native recordings across the full
  account history. The Week/Records clients automatically prepare earlier
  uploads in resumable batches. This backfills existing FitTrackee originals into a separate analysis
  cache, five activities per request with resumable progress and item errors.
  Their originals and privacy remain intact; the bests index includes that cache.
  Multisport FIT needs per-leg handling; current analysis treats one activity.

Privacy filters run after calculation. Owner exports stay complete. Other users
get only allowed HR/GPS, with protected endpoint coordinates removed server-side.
Imported photo EXIF is removed. Media checks current visibility on every request.

Health source enrichment has its own merge version (`health_merge_version: 2`).
It combines fields at duplicate timestamps before calculations, keeps device
distance authoritative, accepts corrected equally sampled Health revisions and
retains existing richer data when later permissions provide less information.
Old derived Health analyses are repaired lazily from retained sources; numerical
method 1.0.0 remains unchanged.

Native recording writes cumulative distance only on measured distance updates,
with explicit anchors at pause/resume boundaries. Heart-rate/power callbacks and
checkpoint timers retain their own samples without repeating stale distance.
Recovery takes the maximum retained distance anchor and reconstructs Health
distance intervals independently of interleaved sensors. Display labels round
fractional seconds once, carrying into minutes/hours; underlying samples and
exports keep their original precision.

## Chart presentation and live recording — October 14

Pace charts use distance over a trailing 30-second window, with a linearly
interpolated boundary. The first reading needs at least five seconds. Recorded
pauses, stops below 0.3 m/s and sampling gaps break the line. A focused pace scale
keeps isolated outliers from flattening the chart, indicates clipped readings,
and offers the complete range. These are display calculations; best efforts,
splits, original recordings and export precision remain unchanged.

Route rendering follows the independent GPS timeline. Sensor-only samples do
not break a route. Explicit privacy redactions and GPS gaps over 60 seconds do;
a reduced preview preserves those breaks even when its sampling is sparse.

Weekly distance uses Monday–Sunday in the requesting user's timezone. Totals
include the entire account history, independent of activity-list pagination.

Native active time uses checkpointed session transitions. An open pause freezes
the clock; sensor callbacks cannot restart it. Raw cumulative device-distance
anchors advance while paused, but those deltas do not increase recorded distance
or reappear on resume. Clock and anchor state survive interruption alongside
the recording. Elapsed time continues through pauses. Physical sensor behaviour
and background endurance still require device validation.
