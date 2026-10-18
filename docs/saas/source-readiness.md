# Source readiness

Source commit: `e114e95471b1bf155454fca108f0730b66a47a01`.

These are source findings. No visual audit, live-provider verification or production-security certification is claimed.

## What exists

| Capability | Source evidence | Conversion implication |
|---|---|---|
| Local web dashboard | `harvey/dashboard.py`, `harvey/web/index.html`, `harvey/web/app.js` | FastAPI and plain HTML/CSS/JavaScript can be retained while the customer experience is redesigned. |
| Discovery, observations and cohorts | `harvey/collectors/discover.py`, `harvey/collectors/profile.py`, `harvey/signals.py`, `harvey/pipeline.py`, `harvey/state.py` | Preserve explainable observations, signal confirmation and cost estimates. |
| Native-mail approval outbox | `Sender._stage_campaign_native`, `Handler._queue_native_reply`, `harvey/gate.py` | Preserve approval and pre-send checks. Verify equivalent protections across every supported adapter. |
| Gmail, Microsoft 365, SMTP and Instantly adapters | `harvey/integrations/`, `Sender.run`, `Handler.run` | Choose a narrow pilot integration set and test each supported path independently. |
| Local inference adapters | `harvey/brain.py`, `harvey/codex.py` | Current operator subscription and credential assumptions require a separate hosted-provider decision. |
| Calendar client | `harvey/integrations/calendar.py` | Placeholder only. Availability returns an empty list and booking returns false. |

## Hosted-service gaps

1. **Identity and authorisation.** The dashboard creates a FastAPI app without account/session authorisation. Its routes include settings updates, worker control, data exports and outbox decisions. The default server binds to `127.0.0.1`, consistent with a local operator tool. Adding an internet-facing URL is not a SaaS conversion.

2. **Workspace isolation.** `harvey/paths.py` derives one `PROJECT_ROOT` from the installed package. Dashboard database, YAML configuration, environment file, token files, PID and logs use shared project paths. `harvey/state.py` models a single operator database. A hosted request, worker job, export and credential lookup all need an authenticated workspace boundary.

3. **Credential custody.** Dashboard settings write plaintext values to the local `.env`; mail adapters use local OAuth-token files. A hosted service needs encrypted tenant secrets, scoped retrieval, refresh-token rotation, disconnect/revocation handling and redacted logs. Masked UI values do not establish encrypted storage.

4. **Worker ownership.** The dashboard tracks subprocess/PID state and background tasks in process globals. A hosted worker must receive immutable workspace/job identifiers, enforce per-workspace quotas and support retry-safe execution. Process globals cannot be the authority for customer ownership.

5. **Sending controls differ by provider.** The checked-in `harvey.yaml` selects Gmail with approval enabled. The configuration class's fallback provider is Instantly. Native sending stages an outbox item and native replies use the approval ladder. Legacy Instantly campaign deployment and reply sending use different paths, including a direct `send_reply` call. A promise that every supported send always waits for approval would overstate the current source.

6. **Self-service commercial functions.** Account signup, workspace membership, invitation roles, hosted onboarding, subscriptions, entitlement enforcement, billing webhooks and account deletion have not been established in this codebase. These are conversion requirements, not existing product claims.

7. **Operational evidence.** No hosted deployment, customer isolation exercise, recovery drill, live mailbox round trip or production calendar booking was run for this checkpoint. Unit/integration tests using mocks cannot replace that evidence.

8. **Distribution notices.** The repository includes Ethan Rogers' MIT notice. `harvey/web/fonts/` contains Geist, Geist Mono and Newsreader binaries; a separate font-licence inventory was not found in the source reviewed. Verify their provenance and include required notices before distributing new assets. Dependency licence review remains open.

## Existing customer-workflow inventory

The source declares thirteen top-level dashboard tabs: Today, Signals, Discover, Companies, Contacts, Campaigns, Outbox, Conversations, Activity, Usage, Settings, Controls and Help. This is an inventory, not a usability verdict. A redesign must preserve access to approval, pause, provider errors, provenance and cost decisions.

## Graph coverage

The hosted Graphify workspace exposes `hythevc/demohatch`, not this repository. Existing local Graphify 0.9.76 extracted a code-only graph from the reviewed commit. The stored extraction has 2,183 nodes and 5,677 edges. Its query loader reports 2,250 nodes after materialising additional graph records.

The graph covers 73 code files including tests. CSS, fonts, documentation and the extensionless licence require direct inspection. The SQL parser was unavailable, so the SQL fixture contributed no symbols. Queries were followed by current-source checks. No semantic extraction or paid model calls were used.
