"""Run: python tests/test_communication.py (no real logs needed)."""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from inspect_ai._util.json import JsonChange
from inspect_ai.event import StoreEvent
from inspect_scout import Transcript

from gl_scanners.communication import communication_scanner

T = "2026-10-09T13:00:0{}+00:00"
JOURNAL = [
    {"run": "r", "sequence": 1, "actor": "a1", "room": None, "kind": "register", "data": {"name": "ada"}, "time": T.format(1)},
    {"run": "r", "sequence": 2, "actor": "a2", "room": None, "kind": "register", "data": {"name": "bo"}, "time": T.format(1)},
    {"run": "r", "sequence": 3, "actor": "a1", "room": "global", "kind": "message", "data": {"text": "I'll take the parser", "reply_to": None, "conversation_kind": "global"}, "time": T.format(2)},
    {"run": "r", "sequence": 4, "actor": "a2", "room": "global", "kind": "read", "data": {"after": 0, "next_after": 3, "delivered": [3]}, "time": T.format(3)},
    {"run": "r", "sequence": 5, "actor": "a2", "room": "dm-x", "kind": "create", "data": {"kind": "dm", "title": "a1 ↔ a2", "members": ["a1", "a2"]}, "time": T.format(4)},
    {"run": "r", "sequence": 6, "actor": "a1", "room": "dm-x", "kind": "join", "data": {}, "time": T.format(4)},
    {"run": "r", "sequence": 7, "actor": "a2", "room": "dm-x", "kind": "join", "data": {}, "time": T.format(4)},
    {"run": "r", "sequence": 8, "actor": "a2", "room": "dm-x", "kind": "message", "data": {"text": "ok, lexer is mine", "reply_to": None, "conversation_kind": "dm"}, "time": T.format(5)},
    {"run": "r", "sequence": 9, "actor": "a1", "room": "global", "kind": "read", "data": {"after": 0, "next_after": 3, "delivered": [3]}, "time": T.format(6)},
    {"run": "r", "sequence": 10, "actor": "a1", "room": "dm-x", "kind": "read", "data": {"after": 0, "next_after": 8, "delivered": [8]}, "time": T.format(7)},
]
STORE = [
    StoreEvent(changes=[JsonChange(op="add", path="/TeamHistory:peers", value=[{"id": a} for a in ("a1", "a2", "a3")])]),
    StoreEvent(changes=[
        JsonChange(op="add", path="/BoardHistory:calls", value=[{"request_id": "x", "action": "send", "completed": True, "result": {"room": "global"}}, {"request_id": "y", "action": "send", "completed": True, "result": {"room": "dm-x"}}]),
        JsonChange(op="add", path="/BoardHistory:journal", value=JOURNAL),
    ]),
]


def transcript(events):
    return Transcript(transcript_id="t", source_type="eval_log", source_id="s", source_uri="u", metadata={}, events=events)


def main() -> None:
    r = asyncio.run(communication_scanner()(transcript(STORE)))
    assert r.answer == "ok" and r.value == 2, r
    m = r.metadata
    assert m["roster"] == [{"id": "a1", "name": "ada"}, {"id": "a2", "name": "bo"}, {"id": "a3", "name": None}]
    evs = m["events"]
    # a1's read of the global room returned only its own post, so it is dropped
    assert [e["kind"] for e in evs] == ["sent", "delivered", "read", "sent", "delivered", "read"]
    assert evs[5]["agent"] == "a1" and evs[5]["record_ids"] == ["m-8"]
    assert m["checks"]["self_deliveries_dropped"] == 1
    glob, dm = evs[0]["send"]["record"], evs[3]["send"]["record"]
    assert glob["to"] == ["all"] and glob["recipients"] == ["a2", "a3"]
    assert dm["to"] == ["a1"] and dm["recipients"] == ["a1"]
    assert evs[2]["agent"] == "a2" and evs[2]["record_ids"] == ["m-3"]
    assert m["checks"]["sent"] == m["checks"]["completed_send_calls"] == 2
    assert m["checks"]["sent_global"] == m["checks"]["completed_global_send_calls"] == 1
    assert m["checks"]["unresolved_dm_rooms"] == 0 and m["checks"]["patch_failures"] == 0

    r2 = asyncio.run(communication_scanner()(transcript(STORE[:1])))
    assert r2.answer == "no_records"

    try:
        from inspect_ai.event import CommunicationEvent  # Inspect main only, for now
    except ImportError:
        print("ok (CommunicationEvent not in this inspect_ai; schema check skipped)")
        return
    for e in evs:
        CommunicationEvent.model_validate(e)
    print(f"ok ({len(evs)} events validate as CommunicationEvent)")


if __name__ == "__main__":
    main()
