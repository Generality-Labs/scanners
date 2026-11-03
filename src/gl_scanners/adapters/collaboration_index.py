"""Convert a collaboration_index board journal into `CommunicationEvent`s.

The collaboration_index harness (github.com/pabloRom2004/collaboration-index) runs
its own message board and exports the board's event journal to the sample store
(`BoardHistory:journal`). This maps that journal onto Inspect's `CommunicationEvent`,
the record inspect_swarm writes natively:

- a `message` row becomes a `sent` event and a `delivered` event. The board commits a
  message and makes it visible in one transaction, so both carry the message's time.
- a `read` row (messages returned to an agent for the first time) becomes a `read` event,
  minus the agent's own posts, which the board also returns.
- `register` names go to the roster; DM rooms resolve to their two members via the
  room's `create` row; global posts go to every other agent on the roster.

Not recorded by the journal, so absent here: refused sends, waits, and reads that
returned nothing new. Message text is replaced by its length and a hash unless include_text.
"""

import hashlib
from typing import Any

SOURCE = "collaboration_index"
CHANNEL = "board"


def _record_id(sequence: int) -> str:
    return f"m-{sequence}"


def convert(store: dict[str, Any], include_text: bool = False) -> dict[str, Any] | None:
    """Return {"roster", "events", "checks"}, or None if the store has no board journal.

    With include_text, each `sent` record carries the message text in `content`.
    """
    journal = store.get("BoardHistory:journal")
    if journal is None:
        return None
    peers = store.get("TeamHistory:peers") or []
    actors = [p["id"] for p in peers]
    names = {e["actor"]: (e.get("data") or {}).get("name") for e in journal if e["kind"] == "register"}
    dm_members = {
        e["room"]: (e.get("data") or {}).get("members", [])
        for e in journal
        if e["kind"] == "create" and (e.get("data") or {}).get("kind") == "dm"
    }

    senders = {e["sequence"]: e["actor"] for e in journal if e["kind"] == "message"}
    events: list[dict[str, Any]] = []
    unresolved_dm = 0
    self_deliveries = 0
    for e in journal:
        data = e.get("data") or {}
        base = {
            "event": "communication",
            "source": SOURCE,
            "channel": CHANNEL,
            "agent": e["actor"],
            "timestamp": e["time"],
        }
        if e["kind"] == "message":
            rid = _record_id(e["sequence"])
            if e["room"] == "global":
                to = ["all"]
                recipients = [a for a in actors if a != e["actor"]]
            else:
                members = dm_members.get(e["room"])
                if not members:
                    unresolved_dm += 1
                    members = []
                recipients = [m for m in members if m != e["actor"]]
                to = list(recipients)
            text = data.get("text") or ""
            reply_to = data.get("reply_to")
            extra = {
                "room": e["room"],
                "sequence": e["sequence"],
                "content_len": len(text),
                "content_sha": hashlib.sha256(text.encode()).hexdigest()[:12],
            }
            events.append(
                base
                | {
                    "kind": "sent",
                    "record_ids": [rid],
                    "send": {
                        "record": {
                            "id": rid,
                            "kind": "message",
                            "sender": e["actor"],
                            "to": to,
                            "recipients": recipients,
                            "content": text if include_text else None,
                            "reply_to": _record_id(reply_to) if reply_to is not None else None,
                        },
                        "rejected": None,
                    },
                    "data": extra,
                }
            )
            events.append(
                base
                | {
                    "kind": "delivered",
                    "record_ids": [rid],
                    "delivery": {"recipients": recipients, "seq": e["sequence"]},
                    "data": {"room": e["room"], "sequence": e["sequence"]},
                }
            )
        elif e["kind"] == "read":
            # the board returns the reader's own posts too; inspect_swarm never shows
            # a member its own messages, so drop them (and count them in checks)
            delivered = data.get("delivered") or []
            own = [s for s in delivered if senders.get(s) == e["actor"]]
            self_deliveries += len(own)
            shown = [s for s in delivered if senders.get(s) != e["actor"]]
            if shown:
                events.append(
                    base
                    | {
                        "kind": "read",
                        "record_ids": [_record_id(s) for s in shown],
                        "data": {"room": e["room"], "sequence": e["sequence"]},
                    }
                )

    calls = store.get("BoardHistory:calls") or []
    sends = [c for c in calls if c.get("completed") and c.get("action") == "send"]
    global_sends = sum(1 for c in sends if (c.get("result") or {}).get("room") == "global")
    return {
        "roster": [{"id": a, "name": names.get(a)} for a in actors],
        "events": events,
        "checks": {
            "journal_rows": len(journal),
            "sent": sum(ev["kind"] == "sent" for ev in events),
            "sent_global": sum(
                ev["kind"] == "sent" and ev["data"]["room"] == "global" for ev in events
            ),
            "completed_send_calls": len(sends),
            "completed_global_send_calls": global_sends,
            "unresolved_dm_rooms": unresolved_dm,
            "self_deliveries_dropped": self_deliveries,
        },
    }
