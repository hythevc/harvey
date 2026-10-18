# Verification record

Source under test: `e114e95471b1bf155454fca108f0730b66a47a01`.

An independent agent ran the committed suite in a separate, clean detached worktree. The final baseline run collected 553 tests: 532 passed, 21 skipped, zero failures and zero errors in 64.157 seconds. Packaging and all four Node-backed dashboard checks passed. The 21 skips require the opt-in real Codex CLI and its localhost test servers; that runtime was not invoked.

The run used Python 3.12, pytest 8.4.2 and pytest-asyncio 0.26.0. Dependencies were installed in a dedicated environment. The runner supplied an allowlisted environment with no provider credentials, disabled unrequested pytest plugins, denied network connects including inherited subprocesses, and blocked reads of known Codex/Claude credential files. Clean checkout, synthetic fixtures and an environment without mail credentials provided the mailbox boundary. An inherited-child network-denial self-test passed. The worktree was clean before and after the run.

The effective pytest arguments were:

```text
-p pytest_asyncio.plugin tests -ra -q --junitxml <evidence>/pytest.xml -o cache_dir=<evidence>/pytest-cache
```

`HARVEY_PACKAGE_TESTS=1` enabled installed-wheel tests. `HARVEY_CODEX_CLI_TESTS` was not enabled. The isolated PATH included the existing Node executable. `PIP_NO_INDEX=1` applied to the test subprocesses.

Evidence includes the JUnit test cases, per-test NDJSON events, run metadata, exact dependency versions and isolation records under `evidence/baseline/`. A compact summary and hashes are retained in `evidence/baseline-summary.json` and `evidence/baseline-sha256.json`.

No hosted SaaS, completed rebrand, live provider round trip or calendar booking is claimed. The baseline above predates the separate mailbox-read error fix. Its focused regression evidence and the integrated candidate's independent verification must be assessed separately.

## Included engine change

Writer commit: `497570a05be24b0f6e1076a382dde9ff774e15bb`, integrated onto the documentation branch by cherry-pick.

Changed application files:

- `harvey/integrations/mail_provider.py` adds `MailboxReadError`.
- `harvey/integrations/gmail.py` rejects failed/malformed inbox and message fetches instead of returning empty or partial results. Invalid JSON uses the existing failure sentinel.
- `harvey/integrations/smtp_mail.py` distinguishes failed IMAP login/select/search/fetch from an empty inbox. It fetches with `BODY.PEEK[]` and marks the requested IDs Seen only after a complete batch. A Seen-acknowledgment failure preserves the complete return value for handling.

The existing `Handler._run_native` failure result and heartbeat send hold are unchanged. Twenty-nine new regression cases exercise adapter errors, genuine empty inboxes, partial-read retry, acknowledgment failure, and actual Handler/heartbeat behavior with mocked external boundaries. The heartbeat cases demonstrate no send during the failure and one send after recovery.

The writer ran:

```text
python -m pytest tests/test_mailbox_read_failures.py tests/test_outbox_native.py tests/test_microsoft.py tests/test_email_wiring.py -q -p no:cacheprovider
```

Result: 112 passed in 6.68 seconds. `git diff --check` passed. The writer's log is `.delivery/decisions/mailbox-fail-closed.md`.

Remaining limitation: successful IMAP Seen acknowledgment still precedes durable Handler processing. A durable inbound ledger and acknowledgment after processing are further reliability work. Pagination, pause races, concurrent dispatch, tenant isolation and the legacy Instantly path are outside this fix.

The integrated candidate must receive an independent source review and full suite run at its exact commit. Those results belong to that immutable commit's review evidence; writer results above are not a substitute.
