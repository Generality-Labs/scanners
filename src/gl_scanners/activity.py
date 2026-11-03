"""What each agent in a multi-agent run spent its model output on, call by call.

For every model call, attributed to the agent span it ran in, records the output and reasoning token
counts and the tool calls the output made (function name and argument size). No text is returned
except, for each tool call, its short `command`/`action` argument if present and the first 60
characters of a shell command, so tool use can be classified (e.g. writing a file vs running tests).
No model is called.
"""

import json
from typing import Any

from inspect_scout import Result, Scanner, Transcript, scanner

SHELL_KEYS = ("cmd", "command", "code")


def _agent_resolver(events: list[Any]):
    spans: dict[str, tuple[str | None, str | None, str]] = {}
    for ev in events:
        if getattr(ev, "event", None) == "span_begin":
            spans[ev.id] = (ev.parent_id, ev.type, ev.name)
    cache: dict[str | None, str | None] = {}

    def agent_of(span_id: str | None) -> str | None:
        start = span_id
        if start in cache:
            return cache[start]
        hops = 0
        name = None
        while span_id is not None and hops < 500:
            parent, kind, nm = spans.get(span_id, (None, None, ""))
            if kind == "agent":
                name = nm  # keep walking: the outermost agent span is the team member
            span_id = parent
            hops += 1
        cache[start] = name
        return name

    return agent_of


def _call_summary(call: Any) -> list[Any]:
    args = call.arguments or {}
    arg_chars = len(json.dumps(args, ensure_ascii=False))
    op = None
    for k in ("command", "action"):
        v = args.get(k)
        if isinstance(v, str) and len(v) <= 24 and "\n" not in v:
            op = v
            break
    head = None
    for k in SHELL_KEYS:
        v = args.get(k)
        if isinstance(v, str) and (op is None or k != "command"):
            head = v[:60]
            break
    return [call.function, arg_chars, op, head]


@scanner(events=["model", "span_begin"], version=1)
def activity_scanner() -> Scanner[Transcript]:
    async def scan(transcript: Transcript) -> Result:
        agent_of = _agent_resolver(transcript.events)
        turns: list[list[Any]] = []
        unattributed = 0
        for ev in transcript.events:
            if getattr(ev, "event", None) != "model" or ev.output is None:
                continue
            agent = agent_of(ev.span_id)
            if agent is None:
                unattributed += 1
            u = ev.output.usage
            msg = ev.output.choices[0].message if ev.output.choices else None
            calls = [_call_summary(c) for c in (msg.tool_calls or [])] if msg else []
            text_chars = len(msg.text or "") if msg else 0
            reasoning_chars = 0
            if msg and isinstance(msg.content, list):
                for c in msg.content:
                    if getattr(c, "type", None) == "reasoning":
                        reasoning_chars += len(getattr(c, "reasoning", "") or "")
            turns.append([
                agent,
                ev.timestamp.isoformat() if ev.timestamp else None,
                u.output_tokens if u else None,
                (u.reasoning_tokens if u else None),
                u.input_tokens if u else None,
                text_chars,
                reasoning_chars,
                calls,
            ])
        return Result(
            value=len(turns),
            answer="ok",
            explanation=f"{len(turns)} model calls, {unattributed} unattributed",
            metadata={
                "columns": ["agent", "time", "output_tokens", "reasoning_tokens", "input_tokens",
                            "text_chars", "reasoning_chars", "tool_calls[function,arg_chars,op,head]"],
                "turns": turns,
                "unattributed": unattributed,
                "model": transcript.model,
            },
        )

    return scan
