"""Programmatic (no-LLM) extraction of the collaboration board journal from MirrorCode swarm runs.

Pablo's harness exports the board's event journal into the sample store
(BoardHistory:journal) inside the solver span, so it appears in StoreEvents.
We replay store changes as JSON patches, then emit a compact journal: message
text is replaced by its length so the result stays small and text-free.
"""

import hashlib
from typing import Any

import jsonpatch
from inspect_scout import Result, Scanner, Transcript, scanner

KEEP = (
    "BoardHistory:journal",
    "BoardHistory:calls",
    "TeamHistory:peers",
    "TeamHistory:run_id",
    "TeamHistory:released",
    "TeamHistory:completed",
    "TeamHistory:objective_completed",
)


def replay_store(events: list[Any]) -> tuple[dict[str, Any], int]:
    """Apply every StoreEvent's JSON-patch changes in order; return final store and #store events."""
    store: dict[str, Any] = {}
    n = 0
    for ev in events:
        if getattr(ev, "event", None) != "store":
            continue
        n += 1
        ops = []
        for c in ev.changes:
            op = {"op": c.op, "path": c.path}
            if c.op in ("add", "replace", "test"):
                op["value"] = c.value  # keep explicit nulls
            if c.from_ is not None:
                op["from"] = c.from_
            ops.append(op)
        for op in ops:
            try:
                jsonpatch.apply_patch(store, [op], in_place=True)
            except (jsonpatch.JsonPatchException, jsonpatch.JsonPointerException):
                # a removed/replaced parent can make a later op unreachable; skip it but count it
                store.setdefault("__patch_failures__", 0)
                store["__patch_failures__"] += 1
    return store, n


def compact(entry: dict[str, Any]) -> dict[str, Any]:
    """Keep structure, drop message text (length + short hash only)."""
    data = entry.get("data") or {}
    row = {k: entry.get(k) for k in ("sequence", "actor", "room", "kind", "time")}
    if entry.get("kind") == "message":
        text = data.get("text") or ""
        row["text_len"] = len(text)
        row["text_sha"] = hashlib.sha256(text.encode()).hexdigest()[:12]
        row["reply_to"] = data.get("reply_to")
        row["conversation_kind"] = data.get("conversation_kind")
    elif entry.get("kind") == "read":
        row["delivered"] = data.get("delivered") or []
    elif entry.get("kind") == "register":
        row["name"] = data.get("name")
    else:
        if data:
            row["data"] = data
    return row


@scanner(events=["store"], version=1)
def message_board_scanner() -> Scanner[Transcript]:
    async def scan(transcript: Transcript) -> Result:
        store, n_store = replay_store(transcript.events)
        journal = store.get("BoardHistory:journal")
        calls = store.get("BoardHistory:calls") or []
        peers = store.get("TeamHistory:peers") or []
        score = transcript.metadata.get("scores") if transcript.metadata else None
        if journal is None:
            return Result(
                value=None,
                answer="no_journal",
                explanation=f"{n_store} store events, keys={sorted(store)[:40]}",
            )
        rows = [compact(e) for e in journal]
        sends = [c for c in calls if c.get("completed") and c.get("action") == "send"]
        n_msg = sum(r["kind"] == "message" for r in rows)
        return Result(
            value=n_msg,
            answer="ok",
            explanation=(
                f"journal={len(rows)} events, messages={n_msg}, "
                f"completed_send_calls={len(sends)}, store_events={n_store}"
            ),
            metadata={
                "run_id": store.get("TeamHistory:run_id"),
                "released": store.get("TeamHistory:released"),
                "completed": store.get("TeamHistory:completed"),
                "objective_completed": store.get("TeamHistory:objective_completed"),
                "peers": [
                    {k: p.get(k) for k in ("id", "tokens", "input_tokens", "output_tokens")}
                    for p in peers
                ],
                "call_counts": _count(calls),
                "completed_send_calls": len(sends),
                "patch_failures": store.get("__patch_failures__", 0),
                "scores": score,
                "journal": rows,
            },
        )

    return scan


def _count(calls: list[dict[str, Any]]) -> dict[str, int]:
    out: dict[str, int] = {}
    for c in calls:
        key = f"{c.get('action')}:{'ok' if c.get('completed') else 'fail'}"
        out[key] = out.get(key, 0) + 1
    return out
