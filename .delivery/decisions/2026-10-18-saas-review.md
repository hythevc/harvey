# Harvey SaaS preparation decision log

UTC recorded: 2026-10-18T08:15:17.472730+00:00
Owner: root integrator
Source repository: https://github.com/hythevc/harvey
Source commit: e114e95471b1bf155454fca108f0730b66a47a01
Working branch: codex/harvey-saas-foundation-20261018

## Scope and ownership

The user authorised creating a SaaS business from this repository, including a new name, UI and branding. This checkpoint records the source audit and implementation requirements. Root owns docs/saas/ and this log. Independent architecture and baseline verification agents use separate detached worktrees and separate evidence directories. No other writer edits this checkout.

## Selected workflow

Global /root/.codex/AGENTS.md was read fresh. Applicable pstack how, architect, blast-radius, unslop and principles for domain ownership, boundaries, independent proof and separate writers apply. Graphify was queried first. Hosted workspace hythevc is connected but exposes only hythevc/demohatch. graph_stats for hythevc/harvey returned unknown repository. Existing Graphify 0.9.76 package successfully built a local code-only graph from this source commit, without installs, paid APIs or semantic extraction. Queries precede source verification.

Graph SHA-256: 9d2fe2ae767a862d2e21da0e46b2fcca5e6f6f65524ee4568892618c17011fc3
Local graph path: /workspace/scratch/bd65ac117d83/harvey-graph/graphify-out/graph.json

## Decisions and limits

- Preserve LICENSE and Ethan Rogers' MIT notice. No claim that inherited public MIT code becomes exclusively owned through rebranding.
- Current checkout is local-operator software, not a proven multi-tenant SaaS. Source and test evidence will determine the conversion requirements.
- Do not configure credentials, mailboxes, calendars, outbound traffic, domains, payments or production deployment.
- Open Design skill was read at /root/.codex/plugins/cache/openai-curated-remote/open-design/0.5.2/skills/open-design-mode/SKILL.md. Its required local runtime, callable tools and MCP registration are absent. Branding, name generation, marketing copy and UI editing are paused under the global mandatory rule. No substitute design generator invoked and no credits spent.
- Antislop timing question was presented. The tool returned no answer. Higher-priority session guidance says continue with best judgement if this optional question receives no answer. Default is during work if design is subsequently unblocked; this is not a separate blocker.
- Baseline tests use an isolated checkout and synthetic/mocked providers. No real provider journey is claimed.

## Graph limitations

Code-only AST graph excludes documentation, CSS, fonts and LICENSE. The SQL parser is missing. These require direct source inspection after graph traversal. Query output may include inferred placeholder/import nodes; query truncation does not establish absence. Graph extraction emitted 2,183 nodes and 5,677 edges; inspect the saved inventory for actual graph representation counts. No semantic or dynamic/runtime relationship proof is claimed.

## Next action

Complete source audit, run baseline tests, record a reviewable documentation checkpoint, and obtain independent verification of its exact commit. To start design work, Open Design must become available or the owner must explicitly waive that requirement for this task.

## Engine prerequisite selected, 2026-10-18T08:20:02.267724+00:00

Source audit identified native Gmail/SMTP mailbox fetch errors returning an empty list. This can let Handler treat reply polling as complete and allow outbound work. A narrow fail-closed fix and regression tests are within the SaaS engine preparation scope and do not depend on design. Delegated writer owns only mail_provider.py, gmail.py, smtp_mail.py, focused tests and its own log, in branch codex/harvey-mailbox-fail-closed-20261018 and separate worktree harvey-mail-hardening. Root will review and integrate only after targeted checks, followed by independent exact-commit verification. No pause-race/concurrent-send changes are included in this slice.

## Integrated engine candidate, 2026-10-18T08:26:45.954713+00:00

Writer commit 497570a05be24b0f6e1076a382dde9ff774e15bb integrated as 48371f7. Root reviewed the source diff and focused tests. Writer ran 112 native mail regressions successfully, including 29 new cases. Full independent verification remains pending until the final candidate commit. Source code and tests are limited to three mail adapters/contract files and one focused test file. IMAP PEEK followed by full-batch Seen acknowledgment preserves prior successful-read behavior while avoiding consumption during a partial fetch. Acknowledgment after durable Handler processing remains open.

Baseline independent suite: 553 collected, 532 passed, 21 intentional real-Codex-CLI skips, zero failures/errors, 64.157 seconds. Evidence committed under docs/saas/evidence/.

Updated local Graphify built from the integrated checkout: 2222 nodes, 5812 edges. SHA-256 7cdd2162d1364081c4bbb243fbbc983752194426d84c4e3694985f6ca299e551. The 83-file code scope includes retained JSON/Python evidence as well as application/tests. Detector skipped secret-scan.json because of its filename; it is a generated zero-findings scan report, not a secret file. Missing SQL parser and excluded CSS/fonts/LICENSE limitations remain. Final graph query confirmed MailboxReadError/get_replies ownership before handoff.

No naming, brand, UI, hosting, provider connections, live sending or payments implemented. Open Design remains the sole design-workflow blocker. Next action: freeze a commit, have the separate reviewer check its source/docs and run full tests, then push a draft PR without merging.
