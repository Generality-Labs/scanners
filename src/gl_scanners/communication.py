"""Who communicated with whom in a multi-agent run, as Inspect `CommunicationEvent`s.

Output is in the shape of Inspect's `CommunicationEvent` (the record inspect_swarm
writes natively), whatever the source. Harnesses that keep their own records are
converted by an adapter in `gl_scanners.adapters`.

Native inspect_swarm logs: Scout's events filter does not accept "communication"
yet (inspect-scout 0.6.2 and main as of 2026-11-03), so this scanner cannot load
them without loading every event. Until it can, it reads harness records only.
"""

from typing import Any

import jsonpatch
from inspect_scout import Result, Scanner, Transcript, scanner

from gl_scanners.adapters import collaboration_index

ADAPTERS = [collaboration_index]


def replay_store(events: list[Any]) -> tuple[dict[str, Any], int, int]:
    """Apply every StoreEvent's JSON-patch changes in order.

    Returns the final store, the number of store events and the number of changes
    that could not be applied.
    """
    store: dict[str, Any] = {}
    n_events = failures = 0
    for ev in events:
        if getattr(ev, "event", None) != "store":
            continue
        n_events += 1
        for c in ev.changes:
            op: dict[str, Any] = {"op": c.op, "path": c.path}
            if c.op in ("add", "replace", "test"):
                op["value"] = c.value  # keep explicit nulls
            if c.from_ is not None:
                op["from"] = c.from_
            try:
                jsonpatch.apply_patch(store, [op], in_place=True)
            except (jsonpatch.JsonPatchException, jsonpatch.JsonPointerException):
                failures += 1
    return store, n_events, failures


@scanner(events=["store"], metadata=False, version=4)
def communication_scanner() -> Scanner[Transcript]:
    async def scan(transcript: Transcript) -> Result:
        store, n_store, failures = replay_store(transcript.events)
        for adapter in ADAPTERS:
            out = adapter.convert(store)
            if out is None:
                continue
            sent = out["checks"]["sent"]
            return Result(
                value=sent,
                answer="ok",
                explanation=f"{adapter.SOURCE}: {sent} sent, {len(out['events'])} events",
                metadata={
                    "source": adapter.SOURCE,
                    "roster": out["roster"],
                    "events": out["events"],
                    "checks": out["checks"] | {"store_events": n_store, "patch_failures": failures},
                    "score": transcript.score,
                },
            )
        return Result(
            value=None,
            answer="no_records",
            explanation=f"no adapter matched; {n_store} store events, keys={sorted(store)[:40]}",
        )

    return scan
