"""Run: python tests/test_affect_keywords.py (no real logs needed)."""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from inspect_ai._util.content import ContentReasoning, ContentText
from inspect_ai.event import ModelEvent, SpanBeginEvent
from inspect_ai.model import ChatCompletionChoice, ChatMessageAssistant, GenerateConfig, ModelOutput
from inspect_scout import Transcript

from gl_scanners.affect_keywords import affect_keywords_scanner


def ev(span, content):
    return ModelEvent(model="m", input=[], tools=[], tool_choice="auto", config=GenerateConfig(), span_id=span,
                      output=ModelOutput(model="m", choices=[ChatCompletionChoice(message=ChatMessageAssistant(content=content))]))


EVENTS = [
    SpanBeginEvent(id="a0", parent_id=None, type="agent", name="agent_0"),
    SpanBeginEvent(id="a1", parent_id=None, type="agent", name="agent_1"),
    ev("a0", [ContentReasoning(reasoning="Test failed again. Damn. Ugh, I'm stuck."), ContentText(text="Retrying.")]),
    ev("a0", "<think>Argh, still 69.</think>Here is the fix."),
    ev("a1", [ContentReasoning(reasoning="", redacted=True, summary="The model is frustrated by failures."), ContentText(text="Phew, all tests pass")]),
]


def main() -> None:
    t = Transcript(transcript_id="t", source_type="eval_log", source_id="s", source_uri="u", metadata={}, events=EVENTS)
    r = asyncio.run(affect_keywords_scanner()(t))
    a0, a1 = r.metadata["per_agent"]["agent_0"], r.metadata["per_agent"]["agent_1"]
    assert a0["reasoning:profanity"] == 1 and a0["reasoning:frustration"] == 2 and a0["reasoning:stuck"] == 1, a0
    assert a0.get("visible:frustration", 0) == 0 and a0["calls"] == 2
    assert a1["redacted_blocks"] == 1 and a1["summary_only_blocks"] == 1 and a1["reasoning:frustration"] == 1
    assert a1["visible:relief"] == 1
    assert r.value == 6
    print("ok")


if __name__ == "__main__":
    main()
