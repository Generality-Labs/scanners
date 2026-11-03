"""Run: python tests/test_activity.py (no real logs needed)."""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from inspect_ai.event import ModelEvent, SpanBeginEvent
from inspect_ai.model import ChatCompletionChoice, ChatMessageAssistant, GenerateConfig, ModelOutput, ModelUsage
from inspect_ai.tool import ToolCall
from inspect_scout import Transcript

from gl_scanners.activity import activity_scanner


def model_event(span, out, reasoning, calls, text=""):
    msg = ChatMessageAssistant(content=text, tool_calls=[ToolCall(id=str(i), function=f, arguments=a) for i, (f, a) in enumerate(calls)] or None)
    return ModelEvent(model="m", input=[], tools=[], tool_choice="auto", config=GenerateConfig(), span_id=span,
                      output=ModelOutput(model="m", choices=[ChatCompletionChoice(message=msg)],
                                         usage=ModelUsage(input_tokens=100, output_tokens=out, total_tokens=100 + out, reasoning_tokens=reasoning)))


EVENTS = [
    SpanBeginEvent(id="solver", parent_id=None, type="solver", name="team"),
    SpanBeginEvent(id="a0", parent_id="solver", type="agent", name="agent_0"),
    SpanBeginEvent(id="a1", parent_id="solver", type="agent", name="agent_1"),
    SpanBeginEvent(id="a0-sub", parent_id="a0", type="agent", name="compaction-helper"),  # nested agent span
    SpanBeginEvent(id="a0-tool", parent_id="a0", type="tool", name="bash"),
    model_event("a0", 50, 20, [("message_board", {"action": "send", "message": "taking the parser"})]),
    model_event("a0-tool", 200, 30, [("bash", {"cmd": "cat > src/parser.py <<'EOF'\nimport re\n...\nEOF"})]),
    model_event("a0-sub", 10, 0, [], text="summary"),
    model_event("a1", 80, 0, [("bash", {"cmd": "pytest -q"}), ("message_board", {"action": "read"})]),
    model_event("orphan", 5, 0, []),
]


def main() -> None:
    t = Transcript(transcript_id="t", source_type="eval_log", source_id="s", source_uri="u", metadata={}, events=EVENTS)
    r = asyncio.run(activity_scanner()(t))
    turns = r.metadata["turns"]
    assert r.value == 5 and r.metadata["unattributed"] == 1, r
    assert [x[0] for x in turns] == ["agent_0", "agent_0", "agent_0", "agent_1", None]  # nested span -> outer agent
    assert turns[0][2:4] == [50, 20]
    assert turns[0][7][0][:3] == ["message_board", turns[0][7][0][1], "send"] and turns[0][7][0][3] is None
    assert turns[1][7][0][0] == "bash" and turns[1][7][0][3].startswith("cat > src/parser.py")
    assert turns[2][5] == len("summary") and turns[2][7] == []
    assert [c[0] for c in turns[3][7]] == ["bash", "message_board"]
    print(f"ok ({len(turns)} turns)")


if __name__ == "__main__":
    main()
