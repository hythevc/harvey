# Mailbox read failure decision log

2026-10-18T08:20:27.441065+00:00

- Base: e114e95471b1bf155454fca108f0730b66a47a01. Branch: codex/harvey-mailbox-fail-closed-20261018.
- Scope: Gmail/SMTP reads must report all failed or partial mailbox reads as failures so Handler and heartbeat hold outbound mail. Successful empty reads stay valid.
- Ownership: mail_provider.py, gmail.py, smtp_mail.py, focused tests, this log only.
- Skills: pstack how, blast-radius, boundary-discipline, fix-root-causes, prove-it-works, unslop; incremental-implementation, TDD.
- Agreed seams from parent task: native adapters get_replies plus Handler/main outbound hold.
- Graphify: existing code-only graph at harvey-graph/graphify-out/graph.json queried before source; base SHA unchanged. Source verifies traversal findings.
- Boundaries: no provider calls, credentials, spend, production changes, UI, product copy or code comments. Independent exact-commit review belongs to parent.

2026-10-18T08:25:37.714058+00:00

- Reproduction: original Gmail HTTP 503 list returned empty success. Initial regression ran 1 failed, 1 passed. Expanded Gmail partial fetch/invalid JSON cases reproduced 5 failures, then 11 passed after the adapter fix.
- SMTP reproduction: status, exception and partial-fetch cases returned empty/partial success, yielding 9 failures and 12 passes before fix.
- Decision: expose MailboxReadError at the mail adapter boundary. Gmail preserves legitimate empty JSON/list successes but rejects failed/invalid list and message reads. Invalid JSON uses the existing None failure sentinel.
- Decision: IMAP PEEKs every requested message and marks Seen only after the full batch parses. No Seen changes occur after list/fetch/parse failure. Acknowledgment failure logs safely and still returns the full collected batch, avoiding loss of successfully fetched replies.
- Parent direction: retain bounded UNSEEN selection and prior successful-read Seen behavior. Do not keep read-only polling, which would risk starving older unread messages behind repeatedly fetched processed messages.
- Remaining limitation: IMAP acknowledgment still precedes durable Handler processing, as in the previous successful path. Durable inbox storage/acknowledgment after Handler success is broader reliability work and is not solved here. Existing query limits and Gmail pagination are unchanged.
- Tests use MockTransport, fake IMAP sessions, temporary state and captured sends. Four cases run the real Handler and heartbeat to prove failures leave approved outbound held and replies unprocessed, followed by one send after recovery. No real provider or credential calls.
- Final command: /workspace/scratch/bd65ac117d83/baseline-evidence/venv/bin/python -m pytest tests/test_mailbox_read_failures.py tests/test_outbox_native.py tests/test_microsoft.py tests/test_email_wiring.py -q -p no:cacheprovider
- Result: 112 passed in 6.68s, including 29 new focused cases. git diff --check passed.
- Handoff: commit this scoped candidate for parent integration. Independent exact-commit review remains pending with parent.
