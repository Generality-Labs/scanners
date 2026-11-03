"""Convert a collaboration_index board journal into `CommunicationEvent`s.

The collaboration_index harness (github.com/pabloRom2004/collaboration-index) runs
its own message board and exports the board's event journal to the sample store
(`BoardHistory:journal`). This maps that journal onto Inspect's `CommunicationEvent`,
the record inspect_swarm writes natively:

- a `message` row becomes a `sent` event and a `delivered` event. The board commits a
  message and makes it visible in one transaction, so both carry the message's time.
- a `read` row (messages returned to an agent for the first time) becomes a `read` event.
- `register` names go to the roster; DM rooms resolve to their two members via the
  room's `create` row; global posts go to every other agent on the roster.

Not recorded by the journal, so absent here: refused sends, waits, and reads that
returned nothing new. Message text is replaced by its length and a hash.
"""

import hashlib
from typing import Any

SOURCE = "collaboration_index"
CHANNEL = "board"


def _record_id(sequence: int) -> str:
    return f"m-{sequence}"


def convert(store: dict[str, Any]) -> dict[str, Any] | None:
    """Return {"roster", "events", "checks"}, or None if the store has no board journal."""
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

    events: list[dict[str, Any]] = []
    unresolved_dm = 0
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
                            "content": None,
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
            events.append(
                base
                | {
                    "kind": "read",
                    "record_ids": [_record_id(s) for s in data.get("delivered") or []],
                    "data": {"room": e["room"], "sequence": e["sequence"]},
                }
            )

    calls = store.get("BoardHistory:calls") or []
    completed_sends = sum(1 for c in calls if c.get("completed") and c.get("action") == "send")
    return {
        "roster": [{"id": a, "name": names.get(a)} for a in actors],
        "events": events,
        "checks": {
            "journal_rows": len(journal),
            "sent": sum(ev["kind"] == "sent" for ev in events),
            "completed_send_calls": completed_sends,
            "unresolved_dm_rooms": unresolved_dm,
        },
    }
