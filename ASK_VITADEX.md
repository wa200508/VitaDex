# Ask VitaDex: first evidence-backed flow

Each saved card has **Ask VitaDex about this organism**. Offline mode retrieves
from that saved card's original factual summary and source records. It does not
silently substitute newer catalog facts, personal notes, or fictional content.

Human review is still pending on the Ohio starter entries, so the default returns
an honest no-reviewed-evidence message. A clearly labeled preview checkbox allows
source-checked facts for testing. That choice does not promote or approve content.

Results show citation identifiers and links. Unsupported questions remain
unanswered. The current evidence is deliberately small: useful for topics such as
dog helper roles, cat whiskers, or robin food, not a general natural-history oracle.

## Optional model selection

Choose **My model (send once)**, enter an HTTPS Chat Completions-compatible endpoint,
a model name, and a session API key. Press **Send once to my model** explicitly.
The question and at most three retrieved fact passages go to that endpoint. There
is no automatic request on discovery, browsing, opening the dialog, or changing a
setting. Endpoints may represent different providers; native provider protocols
that do not support this request/response format need additional adapters.

The model selects passage IDs; it cannot supply new prose for display. VitaDex
assembles the response from the selected stored passages and their actual source
records. Unknown IDs, extra answer fields, malformed output, and oversized replies
are rejected. Source text is labeled untrusted data in the selector prompt, and
no tools, web browsing, or file access are available to the model. Relevance can
still be wrong; selecting a valid passage is not proof that it answers every
aspect of the question. This constrained first flow intentionally favors traceable
facts over fluent but unsupported additions.

Only one worker can be active. Questions, context, reply size, generation length,
and network time are bounded, with no automatic retries. Closing/cancelling or
pausing discards stale output and closes an active response where possible. A
request already received by a server cannot be recalled; connection operations
may finish within their timeout. This is not a streaming/full conversational
memory implementation.

Keys live only in the dialog/provider session and clear on close/pause. They are
not saved to journal data, files, environment variables, or diagnostics. Persistent
provider/key storage is deliberately not implemented; a later version must use
platform-appropriate secure storage if persistence is added. Never commit keys.
Provider error bodies and authorization data are not surfaced in the UI.

Android builds from this batch declare normal **Internet** permission to support
this explicit feature; they still request no camera, microphone, location, or
wake-lock permission. Offline mode makes no model request. The earlier verified
APK at commit `8ed1a24` is an offline preview and predates this interface.

Read-answer speech is deliberate and uses the local system voice. Written answers
and citations remain visible. There is no automatic spoken model response.

## What is verified

Unit tests cover retrieval/review gates, cross-reference integrity, malformed or
invented IDs, injected free-form answer rejection, missing evidence without any
provider call, cancellation, endpoint validation, request budgets, and credential
redaction. Kivy checks cover the offline question UI and clearing keys on close.
No real provider credentials were available or used; live-provider compatibility,
network failure timing, and actual phone behavior remain acceptance gates.
