import time
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest

from harvey.integrations import gmail, smtp_mail
from harvey.integrations.gmail import GmailProvider
from harvey.integrations.mail_provider import MailboxReadError
from harvey.integrations.smtp_mail import SmtpImapProvider


def gmail_provider(monkeypatch, response):
    real_client = httpx.AsyncClient
    transport = httpx.MockTransport(response)
    monkeypatch.setattr(
        gmail.httpx, "AsyncClient",
        lambda **kwargs: real_client(transport=transport, **kwargs),
    )
    provider = GmailProvider(config=None, env=SimpleNamespace())
    provider._access_token = "synthetic-access-token"
    provider._access_expires = time.time() + 3600
    return provider


@pytest.mark.asyncio
async def test_gmail_list_failure_does_not_look_like_an_empty_inbox(monkeypatch):
    provider = gmail_provider(
        monkeypatch, lambda request: httpx.Response(503, json={"error": "offline"}),
    )
    with pytest.raises(MailboxReadError):
        await provider.get_replies()


@pytest.mark.asyncio
async def test_gmail_successful_empty_inbox_is_empty(monkeypatch):
    provider = gmail_provider(
        monkeypatch, lambda request: httpx.Response(200, json={"resultSizeEstimate": 0}),
    )
    assert await provider.get_replies() == []


@pytest.mark.asyncio
@pytest.mark.parametrize("body", [{}, {"messages": []}, {"resultSizeEstimate": 0}])
async def test_gmail_preserves_empty_success_variants(monkeypatch, body):
    provider = gmail_provider(
        monkeypatch, lambda request: httpx.Response(200, json=body),
    )
    assert await provider.get_replies() == []


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", ["network", "invalid_json", "malformed_messages"])
async def test_gmail_listing_failures_are_reported(monkeypatch, failure):
    def response(request):
        if failure == "network":
            raise httpx.ConnectError("mailbox unavailable", request=request)
        if failure == "invalid_json":
            return httpx.Response(200, text="not JSON")
        return httpx.Response(200, json={"messages": None})

    provider = gmail_provider(monkeypatch, response)
    with pytest.raises(MailboxReadError):
        await provider.get_replies()


def gmail_message(message_id):
    return {
        "id": message_id,
        "snippet": "Please stop contacting me.",
        "payload": {"headers": [
            {"name": "From", "value": "Jane <jane@acme.example>"},
            {"name": "Message-ID", "value": f"<{message_id}@acme.example>"},
            {"name": "Subject", "value": "Re: Intro"},
        ]},
    }


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", ["http", "invalid_json", "malformed_message"])
async def test_gmail_partial_fetch_does_not_return_or_consume_partial_results(monkeypatch, failure):
    failed = True

    def response(request):
        if request.url.path.endswith("/messages"):
            return httpx.Response(200, json={"messages": [{"id": "m1"}, {"id": "m2"}]})
        if request.url.path.endswith("/m2") and failed:
            if failure == "http":
                return httpx.Response(503, json={"error": "offline"})
            if failure == "invalid_json":
                return httpx.Response(200, text="not JSON")
            return httpx.Response(200, json={})
        return httpx.Response(200, json=gmail_message(request.url.path.rsplit("/", 1)[-1]))

    provider = gmail_provider(monkeypatch, response)
    with pytest.raises(MailboxReadError):
        await provider.get_replies()
    failed = False
    assert [m.provider_id for m in await provider.get_replies()] == ["m1", "m2"]


class ImapMailbox:
    def __init__(self, failure="", count=2):
        self.failure = failure
        self.seen = set()
        self.messages = {
            str(i).encode(): (
                f"From: Jane <jane@acme.example>\r\n"
                f"Subject: Re: Intro\r\nMessage-ID: <m{i}@acme.example>\r\n"
                f"Content-Type: text/plain\r\n\r\nPlease stop contacting me."
            ).encode()
            for i in range(1, count + 1)
        }
        self.readonly = False
        self.logged_out = False
        self.stores = []

    def login(self, user, password):
        if self.failure == "login_exception":
            raise OSError("mailbox unavailable")
        return ("NO", []) if self.failure == "login_status" else ("OK", [])

    def select(self, mailbox, readonly=False):
        self.readonly = readonly
        return ("NO", []) if self.failure == "select" else ("OK", [b"2"])

    def search(self, charset, query):
        if self.failure == "search":
            return "NO", []
        if self.failure == "search_data":
            return "OK", [None]
        return "OK", [b" ".join(i for i in self.messages if i not in self.seen)]

    def fetch(self, message_id, query):
        if message_id == b"2" and self.failure in ("fetch", "fetch_data", "fetch_exception"):
            if self.failure == "fetch_exception":
                raise OSError("connection dropped")
            return ("NO", []) if self.failure == "fetch" else ("OK", [None])
        if "PEEK" not in query:
            self.seen.add(message_id)
        return "OK", [(b"metadata", self.messages[message_id]), b")"]

    def store(self, message_set, command, flags):
        self.stores.append((message_set, command, flags))
        if self.failure == "store_exception":
            raise OSError("acknowledgment unavailable")
        if self.failure == "store_status":
            return "NO", []
        self.seen.update(message_set.split(b","))
        return "OK", []

    def logout(self):
        self.logged_out = True
        return "BYE", []


def smtp_provider(monkeypatch, mailbox):
    monkeypatch.setattr(smtp_mail.imaplib, "IMAP4_SSL", lambda *args: mailbox)
    return SmtpImapProvider(config=None, env=SimpleNamespace())


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", [
    "login_exception", "login_status", "select", "search", "search_data",
    "fetch", "fetch_data", "fetch_exception",
])
async def test_imap_failures_are_reported(monkeypatch, failure):
    mailbox = ImapMailbox(failure=failure)
    provider = smtp_provider(monkeypatch, mailbox)
    with pytest.raises(MailboxReadError):
        await provider.get_replies()
    assert mailbox.logged_out
    assert mailbox.stores == []


@pytest.mark.asyncio
async def test_imap_successful_empty_inbox_is_empty(monkeypatch):
    mailbox = ImapMailbox(count=0)
    provider = smtp_provider(monkeypatch, mailbox)
    assert await provider.get_replies() == []
    assert mailbox.logged_out


@pytest.mark.asyncio
async def test_imap_partial_fetch_remains_available_for_retry(monkeypatch):
    mailbox = ImapMailbox(failure="fetch")
    provider = smtp_provider(monkeypatch, mailbox)
    with pytest.raises(MailboxReadError):
        await provider.get_replies()
    assert mailbox.seen == set()
    assert mailbox.stores == []
    mailbox.failure = ""
    assert [m.provider_id for m in await provider.get_replies()] == [
        "<m1@acme.example>", "<m2@acme.example>",
    ]
    assert not mailbox.readonly
    assert mailbox.seen == {b"1", b"2"}
    assert len(mailbox.stores) == 1
    assert await provider.get_replies() == []


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", ["store_status", "store_exception"])
async def test_imap_acknowledgment_failure_retains_the_complete_batch(monkeypatch, failure):
    mailbox = ImapMailbox(failure=failure)
    provider = smtp_provider(monkeypatch, mailbox)
    assert [m.provider_id for m in await provider.get_replies()] == [
        "<m1@acme.example>", "<m2@acme.example>",
    ]
    assert mailbox.seen == set()
    assert mailbox.logged_out
    assert len(mailbox.stores) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("provider_name,failure", [
    ("gmail", "list"), ("gmail", "partial"),
    ("smtp", "login_exception"), ("smtp", "fetch"),
])
async def test_native_mailbox_read_failure_holds_outbound_and_leaves_replies_unprocessed(
    monkeypatch, tmp_path, provider_name, failure,
):
    import harvey.main as main_mod
    from harvey.integrations.mail_provider import SendResult
    from tests.test_codex_e2e import Harness, _approved_item, _open_thread
    from tests.test_outbox_native import StubBrain

    harvey = Harness(monkeypatch, tmp_path, provider="claude")
    brain = StubBrain()
    brain.provider_label = "synthetic"
    brain.model = ""
    brain.paused_reason = ""
    brain.preflight = AsyncMock(return_value="")
    brain.is_within_budget = AsyncMock(return_value=True)
    monkeypatch.setattr(main_mod, "Brain", lambda *args: brain)
    harvey.config.channels.email.provider = provider_name
    await harvey.state.init_db()
    await _open_thread(harvey.state, email="jane@acme.example")
    outbox_id = await _approved_item(harvey.state)

    unavailable = True
    mailbox = ImapMailbox(failure=failure)

    def response(request):
        if request.url.path.endswith("/messages"):
            if unavailable and failure == "list":
                return httpx.Response(503, json={"error": "offline"})
            return httpx.Response(200, json={"messages": [{"id": "m1"}, {"id": "m2"}]})
        if unavailable and request.url.path.endswith("/m2"):
            return httpx.Response(503, json={"error": "offline"})
        return httpx.Response(200, json=gmail_message(request.url.path.rsplit("/", 1)[-1]))

    provider = (gmail_provider(monkeypatch, response) if provider_name == "gmail"
                else smtp_provider(monkeypatch, mailbox))
    monkeypatch.setattr(provider, "is_configured", lambda: True)
    provider.send_email = AsyncMock(return_value=SendResult(ok=True, message_id="sent-1"))
    harvey.mail = provider
    first_id = "m1" if provider_name == "gmail" else "<m1@acme.example>"
    held = {}

    async def recover():
        nonlocal unavailable
        held["send_count"] = provider.send_email.await_count
        held["processed"] = await harvey.state.is_reply_processed(first_id)
        held["outbox_status"] = (await harvey.state.get_outbox_item(outbox_id))["status"]
        held["imap_stores"] = list(mailbox.stores)
        unavailable = False
        mailbox.failure = ""

    await harvey.run_cycles(2, between={1: recover})

    assert held == {
        "send_count": 0, "processed": False, "outbox_status": "approved", "imap_stores": [],
    }
    assert await harvey.state.is_reply_processed(first_id)
    assert (await harvey.state.get_outbox_item(outbox_id))["status"] == "sent"
    provider.send_email.assert_awaited_once()
    assert provider.send_email.await_args.args[0] == "bob@beta.com"


@pytest.mark.asyncio
async def test_imap_partial_parse_failure_does_not_mark_any_message_seen(monkeypatch):
    mailbox = ImapMailbox()
    mailbox.messages[b"2"] = b"Subject: incomplete\r\n\r\nNo sender header."
    provider = smtp_provider(monkeypatch, mailbox)
    with pytest.raises(MailboxReadError):
        await provider.get_replies()
    assert mailbox.stores == []
    assert mailbox.seen == set()
    assert mailbox.logged_out


@pytest.mark.asyncio
async def test_imap_connection_failure_is_reported(monkeypatch):
    def unavailable(*args):
        raise OSError("connection unavailable")

    monkeypatch.setattr(smtp_mail.imaplib, "IMAP4_SSL", unavailable)
    provider = SmtpImapProvider(config=None, env=SimpleNamespace())
    with pytest.raises(MailboxReadError):
        await provider.get_replies()
