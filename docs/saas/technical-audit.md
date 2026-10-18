# SaaS readiness audit

Source commit: `e114e95471b1bf155454fca108f0730b66a47a01` in `hythevc/harvey`. Review date: 18 October 2026. This is a source audit, not runtime verification or a production security assessment. No application code, providers, accounts or infrastructure changed.

The repository contains a local sales agent with a useful working model: discover companies, collect approved signals, select prospects, write sequences, review native-mail drafts, poll replies and record activity. A hosted subscription product needs authentication, tenant isolation, a different operating model and billing. Changing the name and dashboard alone does not provide those controls.

## Graph and evidence boundary

Graphify was queried before source exploration. The parent built it from the fresh source commit with `python -m graphify extract . --code-only --out ../harvey-graph --no-cluster`. The JSON contains 2,183 nodes and 5,677 edges across 73 detected code files including tests. The query CLI adds placeholder/import records and reports 2,250 nodes. SQL parsing was unavailable. CSS, fonts and LICENSE were outside the detector scope and were inspected directly after the graph gate. Broad queries truncated results, so this audit verifies each material claim against source. `evidence/graph-query.txt`, `evidence/route-inventory.csv` and `evidence/source-inventory.json` record the query, route census and SHA-256 inventory.

## Current architecture and requirements

| Area | Source finding | Requirement before hosted SaaS |
|---|---|---|
| Authentication and sessions | `dashboard.py:43` creates `FastAPI` without authentication dependencies. The 36 explicit routes have no account/session checks or route dependency arguments. `start_dashboard` binds loopback by default at `dashboard.py:1336`. `app.js:128` uses plain same-origin fetch. OAuth in Gmail/Microsoft connects a mailbox, not a product user. | Authenticate every data/control request. Add verified user accounts, expiring sessions, logout/revocation and authorization for workspace members. Test unauthenticated reads/writes and cross-user ID access before exposing a public host. |
| Tenant isolation | `paths.py:12` fixes the checkout root. `state.py:27` and `dashboard.py:25` select the same `data/harvey.db`. Companies/prospects/outbox/settings have no SaaS workspace ownership keys at `state.py:55`, `71`, `258`, `287`. Dashboard queries read all rows, such as `dashboard.py:688`, `793`, `808`. | Introduce a required workspace context through requests, jobs, storage and integrations. Choose tenant-specific worker/data volumes or a tenant-keyed database with enforced access boundaries. Prove two tenants cannot read, approve, export, modify or send each other's records. Never derive authority from a client-supplied workspace ID alone. |
| Secret storage | `dashboard.py:80` reads `.env`, and `:92` writes plaintext values then mutates process environment through `load_dotenv(...override=True)`. Settings GET returns presence flags for secrets at `:254`, which is useful. Gmail and Microsoft token JSON paths are global at `gmail.py:37` and `microsoft.py:48`; token saves write plaintext JSON and attempt chmod 600 at `gmail.py:58` and `microsoft.py:88`. | Store provider credentials per workspace/mailbox in an encrypted secret store. Support revoke/disconnect and key rotation. Do not let tenant configuration change shared process environment. Keep secrets out of responses, logs and support exports. |
| Worker ownership | `dashboard.py:46` and `:841` hold process/task state in module globals. `:455` spawns one `python -m harvey` child; `:472` writes one PID; `:489` kills it. Discovery uses an in-process task at `:954`. `main.py:168` loads one config/env and creates one StateManager and agent set. | Put jobs behind durable scheduling with one active worker lease per workspace/mailbox. Persist run identity, cancellation and recovery. Run safe handlers after restarts. Do not expose OS process start/stop as the public tenant control contract. |
| Database lifecycle | SQLite uses WAL and a busy timeout at `state.py:450-478`; these support local concurrency. Schema upgrades use `PRAGMA user_version` and linear migration scripts. They do not create an application-level send lease. | Version and test migrations, backup/restore and rollback. Prove concurrency semantics and data deletion. A hosted database migration is a deployment decision, not a prerequisite for all private local pilots. |
| Signup, onboarding and billing | `get_setup_status` checks local venv, `.env`, mailbox tokens and YAML at `dashboard.py:119`. `index.html:207` requires a terminal Gmail OAuth command. No product signup, invitations, subscription checkout, entitlement lifecycle or payment webhook handler exists in the 36 routes. Billing/subscription matches elsewhere concern data providers and the operator's AI plan. | Build workspace signup and product/ICP/mailbox onboarding. Add plan entitlements and a usage ledger independent of AI-provider quota. Implement signed, idempotent billing webhooks plus cancellation and failed-payment behavior. Use USD base prices and local-currency display per the owner's standing rule. Do not invent a price until hosted unit costs are measured. |
| Model runtime | `Brain.think` invokes local Claude CLI with tools disabled and strict MCP configuration at `brain.py:249-262`. Codex is an opt-in local subscription adapter. The product assumes the operator's local login/plan rather than a hosted model API. | Choose and cost a supported hosted runtime or a customer-managed worker model. Verify provider contract/plan suitability separately. Local subscription quota and zero marginal token cost are not verified hosted SaaS economics. Preserve tool isolation and fail-closed handling. |
| Privacy lifecycle | The API exports prospects at `dashboard.py:768`; there are no account/workspace deletion or retention routes in the inventory. State stores prospect identities, conversations, actions and provider references. | Specify deletion, retention, export and backup-erasure behavior. Prove deletion removes credentials and stops queued jobs/sends. Preserve only a documented minimum suppression record where required; do not promise permanent suppression and complete erasure without a defined policy. |
| Meeting booking | `integrations/calendar.py:9` calls itself a placeholder, and `:15`/`:20` are unimplemented availability/booking functions. Handler advances a conversation stage on meeting language at `handler.py:563`. | Treat booking as incomplete. Require provider-backed availability, timezone handling, conflict-safe booking, retries and a recorded event ID before claiming booked meetings. |

## Mail controls to preserve and close

The shipped `harvey.yaml:50-54` selects Gmail, requires approval, sends only to verified addresses and sets a bounce threshold. The Pydantic fallback provider at `config.py:76` is Instantly. These are different paths and must not be reported as one blanket approval guarantee.

| Control | Source evidence and limit | Acceptance requirement |
|---|---|---|
| Native draft approval | `Sender._stage_campaign_native`, `sender.py:357-400`, chooses pending_review by default. `Handler._queue_native_reply`, `handler.py:473-488`, uses the same flag. Setting require_approval false stages approved rows. | Only an authorized reviewer can approve a draft. Record reviewer identity, exact approved content/version and timestamp. Content/recipient changes must invalidate approval. |
| Delivery gate | `gate.py:49-107` checks recipient/record match, verified status for sequence sends, subject/body, merge tags, phrase and link limits and HTML. `sender.py:489` calls it before native send. | Preserve deterministic checks across every provider. Test both cold sequences and replies. These checks do not establish marketing consent or legal permission. |
| Stop-on-reply and bounces | `handler.py:215` cancels queued sends before classification. `:280-304` handles opt-out/escalation without auto-reply. `:423-467` invalidates bounced addresses and pauses after its threshold. `main.py:303-319` holds sends if reply handling fails. | Prove unread reply, opt-out, bounce and provider outage paths on every provider. A global mutable setting must become workspace/mailbox-scoped. |
| Legacy Instantly | `sender.py:78-106`, `:127-275` deploys/activates campaigns directly. It does not use the native outbox approval, native deterministic content gate or native kill-switch path. `handler.py:339-346` sends legacy replies directly. | Unify approval, policy gates, pause and audit checks for Instantly, or exclude it from the initial hosted release. |
| Pause timing | Native `_run_native` checks the kill switch at `sender.py:321`; `_drain_due` iterates its captured due list and sleeps between sends at `:467-580` without another pause read. | Recheck pause and suppression immediately before each external send. Test pausing after the first item of a multi-item drain. Source evidence supports the gap; no race was reproduced here. |
| Concurrent/uncertain sends | `_drain_due` reads approved rows at `sender.py:440`, sends externally at `:528`, then marks sent at `:541`. The uniqueness index at `state.py:280` prevents duplicate sequence rows, not two workers sending the same row. `SendResult` has only ok/error at `mail_provider.py:28`. | Claim/lease each send atomically. Add attempt IDs, idempotency where supported and a distinct uncertain outcome with reconciliation. Test concurrent workers and a crash after provider acceptance before the sent write. A duplicate was not reproduced in this audit. |
| Mailbox-read failures | Gmail `_request` converts HTTP errors to None at `gmail.py:110-125`, while `get_replies` returns [] when listing fails at `:175-181`. SMTP returns [] on fetch exceptions at `smtp_mail.py:89-95`. `Handler._run_native` treats a returned empty list as complete at `handler.py:378-421`. | Use typed empty-success versus read-failure results. A mailbox outage must hold outbound until stop-on-reply can run. Add failure tests for Gmail and SMTP, not only exception-raising adapters. |

## Source-only UI workflow inventory

No browser or screenshot review was performed. This inventory describes handlers and data contracts, not visual quality.

| Existing section | Source entry and actions |
|---|---|
| Today | `index.html:49`, `app.js:182`; `/api/today`, setup status, recent runs/activity. |
| Signals and cohort | `index.html:78`, `app.js:330`, `:404`, `:586`, `:627`; confirm/reject signal codes, require/exclude codes and preview companies. |
| Discover | `index.html:98`, `app.js:428`, `:492`, `:526`, `:543`; provider menu, estimated cost, run and stop. |
| Companies and contacts | `index.html:139`, `:145`; `app.js:1172`, `:1198`, `:1245`; company drilldown, contact rows, CSV exports and feedback. |
| Campaigns | `index.html:157`, `app.js:1268`; reads campaign/sequence data and offers feedback. |
| Outbox | `index.html:163`, `app.js:1042`, `:1105`, `:1151`, `:1158`, `:1165`; review, approve/reject, approve-all, pause/resume. Keyboard actions at `app.js:1139`. No draft-edit endpoint in the route inventory. |
| Conversations, activity, usage | `index.html:178`, `:184`, `:190`; `app.js:1297`, `:1324`, `:954`; reads threads, activity and provider quota/token counters. |
| Settings | `index.html:199`, `app.js:667-790`; saves global mailbox/provider secrets and tests an Instantly key. |
| Controls and help | `index.html:291`, nav at `:42-43`; process start/stop/status/logs and local setup guidance. |

## Licensing and attribution

`LICENSE:1-21` is MIT with `Copyright (c) 2026 Ethan Rogers`. It explicitly permits use, modification, sublicensing and sale, subject to retaining the copyright and permission notice in copies or substantial portions. Keep this upstream notice in source and distribution. A new brand does not erase the upstream attribution. The repository's own new work can be tracked separately; dependency and asset notices still need review.

`pyproject.toml:43-47` points at the upstream Ethan repository. Its package-data section includes all `web/fonts/*`. Three binary font files are present. `app.css:17-27` identifies Newsreader, Geist and Geist Mono. The tracked file census found only the root LICENSE, with no standalone font OFL/license/notice files. FontTools was available but WOFF2 metadata decoding failed because Brotli is missing. Therefore exact font provenance and notices remain unverified. This audit did not download licenses or install a decoder. Resolve those notices before redistributing the fonts.

## Minimum evidence for the hosted candidate

1. Two test tenants and two reviewer roles exercise every data/control route and every worker job with cross-tenant IDs.
2. Session expiry, logout, invitation revocation and secret disconnect stop access without dropping tenant boundaries.
3. Every enabled mail provider passes approval, content-change, pause, suppression, reply outage, concurrent-worker and uncertain-send tests.
4. A complete signup-to-workspace-to-product-to-mailbox-to-approved-draft journey runs in staging. Use a fake mailbox for tests unless live sending is separately authorized.
5. Billing entitlements and webhook replay tests pass, with provider costs and measured gross margin recorded before choosing a subscription price.
6. Backup/restore, tenant deletion, queue cancellation and operational recovery have recorded outcomes.
7. Calendar remains excluded from booking claims until a real booking integration passes conflict and retry tests.
8. Upstream MIT and verified third-party asset/dependency notices are included in the release candidate.

No runtime, tenancy, billing or provider integration pass is claimed by this source audit. Root is collecting executable test evidence separately. Required Open Design runtime availability remains the parent's reported blocker for naming, product copy, UI and branding work.
