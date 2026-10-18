# SaaS conversion checkpoint

Prepared for Jaime Henriques on 18 October 2026.

Repository reviewed: `hythevc/harvey` at `e114e95471b1bf155454fca108f0730b66a47a01`.

Harvey is a local sales-agent codebase with implemented discovery and mail workflows. It is not an established hosted SaaS. This checkpoint records what can be reused and the work required to create a commercial service. It does not contain a finished rebrand or a deployed product.

The branch also includes one engine prerequisite: Gmail and SMTP mailbox-read failures now propagate to the existing reply-handler failure path, holding outbound mail for that cycle. IMAP collects the whole batch before marking it seen, so a partial fetch remains retryable. The source audit describes the starting commit; [verification](verification.md) distinguishes the included fix from those baseline findings.

- [Source readiness](source-readiness.md) records the current implementation and gaps.
- [Technical audit](technical-audit.md) provides the detailed source references and mail-control findings.
- [Implementation plan](implementation-plan.md) defines the hosted conversion and acceptance evidence.
- [Ownership and delivery boundaries](ownership-and-boundaries.md) records licence attribution and the blocked design workflow.
- [Verification](verification.md) records executable evidence and its limits.

## Commercial hypothesis

Start with small sales teams and agencies prospecting local businesses. This is a hypothesis drawn from the existing business-discovery, website-observation and cohort functionality. Customer demand and willingness to pay have not been validated.

The first pilot should prove one complete customer job: define a target market, find suitable businesses, inspect the supporting observations, draft relevant outreach, approve it, and handle the response. Keep a human decision before outbound messages. Calendar booking must wait for an implemented integration.

Revenue should come from a workspace subscription with explicit usage limits. Price is undecided. Use a USD base price with local-currency display and validate the owner's 50% gross-margin floor against measured model, enrichment, mailbox, infrastructure, payment and support costs. Do not advertise unlimited usage or assume consumer subscriptions make hosted inference free.

## Current delivery status

| Item | Status |
|---|---|
| GitHub source access | Confirmed |
| Local architecture graph | Built and queried |
| Repository licence | MIT notice inspected and retained |
| Source-only SaaS audit | Recorded |
| Baseline tests | 532 passed, 21 intentional real-CLI skips |
| Mailbox-read failure fix | Implemented; 112 focused/native regressions passed, including 29 new cases |
| New product name and clearance | Not started |
| Brand assets and redesigned UI | Blocked by the required Open Design runtime |
| Hosted authentication, tenant isolation and billing | Not implemented |
| Deployment, live mail, payments and customer integrations | Not performed |

The next executable implementation step is account and workspace isolation. Design generation also requires Open Design to be connected, or an explicit owner exception for this task. No global instructions or account configuration were changed.
