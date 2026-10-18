# Hosted conversion plan

This is an implementation specification. The items below have not been built by this checkpoint.

## Architecture choice

Two viable shapes were considered.

| Option | Benefit | Cost or limit |
|---|---|---|
| Hosted application and managed workers | Browser signup and a conventional workspace subscription | Requires identity, durable tenant isolation, credential custody, a supported inference contract and metering. |
| Hosted control plane with a local customer runner | Reuses the current local subscription and filesystem model | Requires runner installation, connectivity and lifecycle support. Provider permission for each use still needs review. |

Use the hosted application as the target because the owner asked for SaaS. Preserve the existing local engine until the hosted boundaries are proven. A local runner remains an alternative if measured economics or provider terms make the hosted model unsuitable.

A possible deployment uses Vercel for the frontend, Railway for API/workers and Neon PostgreSQL for durable data, matching the owner's existing infrastructure preferences. No accounts or resources were provisioned. Final selection depends on region, cost and required data handling.

## Contracts and ownership

- `User` authenticates through an established identity service. Server-side membership resolves a `WorkspaceContext`; request JSON cannot choose an arbitrary workspace.
- `Workspace` owns product configuration, target criteria, prospects, observations, campaigns, outbox items, conversations, integration references, quotas and entitlements.
- `Job` has a workspace, idempotency key, status and attempt history. Workers retrieve only that workspace's data and secrets.
- `OutboxItem` has an explicit state transition from draft to pending review, approved, dispatching, sent, failed or uncertain. Changes after approval require a new review. A retry must not turn an uncertain provider outcome into a duplicate send.
- `IntegrationConnection` stores provider identity and an encrypted secret reference. Authentication and token refresh belong to the provider adapter; workspace authorisation belongs to the service boundary.
- `Subscription` owns billing state and product limits. Payment-webhook identifiers are deduplicated. The browser never decides entitlement.

Keep existing Python import paths, CLI commands and database filenames compatible during the first customer-facing rename. A bulk replacement of `harvey` would affect package imports, installed scripts, environment switches, OAuth files, state and tests. Rename those separately with migration evidence if there is a product reason.

## Delivery gates

| Gate | Implementation | Acceptance evidence |
|---|---|---|
| 1. Identity and isolation | Signup/login, workspace membership, roles, PostgreSQL migration and scoped repositories | Two users in different workspaces cannot read or mutate each other's lists, settings, outbox, exports, job status or integration references. Missing/expired sessions fail closed. A forbidden workspace ID in a URL/body is rejected. |
| 2. Secrets and worker context | Encrypted secret storage, scoped OAuth callback/refresh, durable jobs, quotas and redaction | Cross-workspace secret access is denied; disconnect revokes use; refresh rotation persists correctly; retry and restart preserve the owning workspace. Logs contain no raw secrets. |
| 3. One complete sales workflow | Product setup, ICP, confirmed signals, costed discovery, evidence review, drafting and approval | A synthetic customer completes the journey using mocks/sandbox accounts. No paid collector runs without its cost decision. Approval records user, workspace, content version and time. |
| 4. Consistent mail protection | One dispatcher contract for all supported pilot providers; pause, opt-out, bounce and duplicate handling | Native and any retained Instantly path obey the same promised approval policy. Pause blocks dispatch; opt-out survives retries; provider uncertainty does not create a second send. Unsupported paths are excluded from the pilot. |
| 5. Brand and interface | Cleared name, brand assets, information architecture, onboarding, responsive app and marketing site | Open Design workflow or owner-authorised alternative completes. Real desktop/mobile screenshots, keyboard and focus checks, error/empty/loading states, and a recorded interaction journey support the result. No fabricated claims or dead CTAs. |
| 6. Commercial service | Test-mode billing, server entitlements, metering, limits, account export/deletion and recovery | Duplicate and out-of-order test webhooks cannot duplicate entitlements. Cancellation is reflected correctly. Tenant export/deletion and a backup restore are demonstrated. Measured unit economics pass the 50% margin floor. |
| 7. Controlled release | Staging deployment, monitoring and a reviewed pilot release | Exact commit, test results, mobile/desktop evidence, mailbox round trip and rollback/recovery evidence. Owner separately approves live domains, payments, spending and customer outreach. |

Calendar booking is a separate integration gate. Until implemented and tested, use an existing scheduling link or human follow-up and do not represent a meeting as booked merely because a conversation was classified as interested.

## Commercial validation

Validate the proposed audience with founder-led discovery before fixing a pricing page. Measure time to first qualified list, proportion of drafts accepted without edits, verified deliverability status, response handling quality and operator time per workspace. Distinguish actual bookings from positive replies.

Record variable costs per workspace in USD and test realistic high-usage customers. At a 50% gross-margin floor, allowed cost is at most half net revenue. Include external usage, compute, storage, payment fees and directly attributable support. No selling price or margin is proven yet.

## Next implementation slice

Build gate 1 in an isolated branch using synthetic users and data. Keep mail and paid collectors mocked. In parallel, unblock the design runtime, generate a name shortlist, check obvious company/product conflicts, obtain domain/trademark evidence, then create and review the visual directions. No domain is to be purchased automatically.
