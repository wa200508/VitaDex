# Battery conservation

VitaDex should leave the user free to explore without worrying that their field
guide is draining their phone. Minimize energy across the whole interaction,
including sensors, CPU/GPU, memory, storage, radio use, speech, and display.
Power use is a feature acceptance criterion from the start of implementation.

These are product requirements. The current computer preview has no real sensing
pipeline, and mobile energy consumption has not been measured. No runtime power
optimization is implied by this document.

## Default behavior

- Sensors are off until the user explicitly starts discovery. Microphone capture
  is disabled by default and requires a deliberate choice to enable it.
- Capture sessions have an explicit end, a maximum duration, and clear status.
  Release camera/microphone resources on completion, cancellation, error,
  backgrounding, or device lock. Do not retain preview streams between sessions.
- No continuous background recognition, periodic discovery polling, passive
  listening, or always-on location tracking in the default product.
- Do not hold the display on or acquire persistent wake locks. Respect the user's
  screen timeout, battery saver, and thermal restrictions.

## Recognition and duplicate encounters

Use the smallest input resolution and shortest audio sample that meet measured
identification quality. Prefer a still image or a short sample over continuous
video/audio inference. Limit concurrency, bound queues, and cancel obsolete jobs.
Never loop indefinitely trying to obtain a confident match; show uncertainty and
let the user choose whether to try again.

Cache reusable model state within a bounded session where loading it repeatedly
would waste energy, then release it according to measured memory/power tradeoffs.
Choose models using both identification quality and measured energy/latency.
Local processing helps privacy and offline operation, but may use more energy
than a carefully bounded remote request. Measure the complete cost, including
radio activation and uploads, before choosing an execution path.

An organism's saved discovery suppresses repeated automatic narration and card
creation. This alone does **not** save the energy needed to capture and recognize
it. Sensor duration, sampling, and inference frequency must be bounded before
recognition, rather than relying only on a duplicate check afterward.

## Speech, cards, and interface

- Read a short saved introduction for a first discovery; do not generate a fresh
  LLM introduction for every encounter. Replays are explicit user actions.
- Use installed system voices where available. Do not synthesize speech, retry,
  or download voices automatically in the background. A missing voice should
  leave the written card usable and offer a deliberate retry.
- Stop or suspend speech appropriately on cancellation and lifecycle changes,
  and release native speech resources. Native cancellation/ownership adapters
  are now implemented, but actual-device validation remains outstanding. Desktop
  or mocked tests do not close this requirement.
- Keep static screens event driven. Avoid timers that rebuild unchanged cards,
  idle animations, continuous canvas updates, and unnecessarily high render rates.
  Choose render behavior using interaction and energy measurements.
- Reuse local card snapshots and reviewed content. Build/update collection views
  when their data changes, and load visible content incrementally as collections
  grow. Avoid rewriting a large journal or rebuilding every tile for one change.

## Retrieval, chat, and network use

- Chat and optional spoken answers run on request, not automatically on detection.
  Keep questions grounded in cached, reviewed source passages where possible.
- Reuse source text and retrieval indexes. Invalidate caches by content/version
  changes rather than downloading references whenever a card opens.
- Bound prompt/context size, output length, concurrent requests, and retries.
  Cancel superseded requests; do not repeatedly retry when offline.
- Batch optional content refreshes and use OS-managed scheduling when background
  work is justified. Offer download choices for substantial model/content assets;
  do not silently start them on mobile data or low battery.
- A preference for local execution is not permission to run an expensive local
  LLM continuously. Provider and model choices must account for total energy.

## Verification before mobile release

Use platform energy profilers and activity traces on representative real devices.
Record device, OS, battery-saver state, thermal state, brightness, connectivity,
workload duration, model/version, and cache state so comparisons are repeatable.
Compare against an idle app with the same screen settings. Battery percentage
alone is too coarse to characterize short operations reliably.

Measure these scenarios separately:

| Scenario | Evidence required |
| --- | --- |
| Open journal, no interaction | No recurring discovery, inference, or network jobs; no unexplained CPU/GPU activity |
| App backgrounded or phone locked | Camera/microphone released; no continuing recognition or app-requested wake lock |
| One new discovery | Bounded capture/inference, one saved card, one requested introduction |
| Repeated known organism | No repeated announcement/card; sensing still stays within the capture budget |
| Cancelled or failed capture | Resources released; no retry loop or abandoned worker |
| Speech and interruption | Playback/resources stop as intended; no repeated synthesis or hidden queue growth |
| Browse a large collection | Smooth interaction without rebuilding or loading all offscreen content unnecessarily |
| One source-grounded question | Bounded retrieval/provider work; cancellation and offline behavior verified |

Before release, set numerical energy, latency, and session-duration budgets from
these measurements for supported device classes. Record baselines and compare
subsequent builds using the same workloads. Investigate regressions rather than
claiming a universal battery-life figure from a desktop test or one phone.
