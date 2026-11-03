"""Keyword counts for emotional language in each agent's reasoning and visible output. No model is called.

A crude, transparent baseline: per agent, counts of lexicon hits per category in readable reasoning and in
visible text, characters of each, how much reasoning was redacted or summary-only, and a sample of short
snippets around hits so they can be read. Agents are the outermost agent span of each model call, as in
`activity_scanner`.
"""

import random
import re
from collections import defaultdict
from typing import Any

from inspect_scout import Result, Scanner, Transcript, scanner

from gl_scanners.activity import _agent_resolver

LEXICON = {
    "frustration": r"\bfrustrat\w*|\bannoy\w*|\bugh+\b|\bargh+\b|\bsigh\b",
    "desperation": r"\bdesperat\w*|\bhopeless\w*|\bgiv(?:e|ing) up\b|last resort|running out of (?:time|budget|tokens|steps)",
    "anxiety": r"\bI'?m (?:now |getting |a bit |really )?(?:worried|nervous|anxious|scared|afraid)\b|\bstressed\b",
    "profanity": r"\bdamn\w*|\bcrap\b|\bshit\w*|\bfuck\w*|\bwtf\b",
    "stuck": r"\bI'?m (?:so |really |completely )?stuck\b|\bgoing (?:around )?in circles\b",
    "relief": r"\brelie(?:f|ved)\b|\byay+\b|\bwoo+hoo+\b|\bhooray\b|\bphew\b",
}
_RX = {k: re.compile(v, re.I) for k, v in LEXICON.items()}
_THINK = re.compile(r"<think>(.*?)</think>", re.S)


def _texts(msg: Any) -> tuple[str, str, int, int]:
    """Readable reasoning, visible text, and reasoning blocks redacted / summary-only."""
    reasoning, visible, redacted, summary_only = [], [], 0, 0
    content = msg.content
    if isinstance(content, str):
        reasoning += _THINK.findall(content)
        visible.append(_THINK.sub("", content))
    else:
        for c in content or []:
            if getattr(c, "type", None) == "reasoning":
                if c.redacted:
                    redacted += 1
                    if c.summary:
                        summary_only += 1
                        reasoning.append(c.summary)
                else:
                    reasoning.append(c.reasoning)
            elif getattr(c, "type", None) == "text":
                reasoning += _THINK.findall(c.text)
                visible.append(_THINK.sub("", c.text))
    return " ".join(reasoning), " ".join(visible), redacted, summary_only


@scanner(events=["model", "span_begin"], version=1)
def affect_keywords_scanner(max_quotes_per_category: int = 40, seed: int = 0) -> Scanner[Transcript]:
    async def scan(transcript: Transcript) -> Result:
        rng = random.Random(seed)
        agent_of = _agent_resolver(transcript.events)
        per: dict[str, dict[str, Any]] = defaultdict(lambda: defaultdict(int))
        quotes: dict[str, list[dict[str, Any]]] = defaultdict(list)
        seen: dict[str, int] = defaultdict(int)
        for ev in transcript.events:
            if getattr(ev, "event", None) != "model" or ev.output is None or not ev.output.choices:
                continue
            agent = agent_of(ev.span_id) or "_unattributed"
            reasoning, visible, redacted, summary_only = _texts(ev.output.choices[0].message)
            a = per[agent]
            a["calls"] += 1
            a["reasoning_chars"] += len(reasoning)
            a["visible_chars"] += len(visible)
            a["redacted_blocks"] += redacted
            a["summary_only_blocks"] += summary_only
            for channel, text in (("reasoning", reasoning), ("visible", visible)):
                for cat, rx in _RX.items():
                    for m in rx.finditer(text):
                        a[f"{channel}:{cat}"] += 1
                        key = f"{channel}:{cat}"
                        seen[key] += 1
                        snippet = {"agent": agent, "time": ev.timestamp.isoformat() if ev.timestamp else None,
                                   "text": text[max(0, m.start() - 160): m.end() + 120]}
                        q = quotes[key]
                        if len(q) < max_quotes_per_category:
                            q.append(snippet)
                        else:  # reservoir sample
                            j = rng.randrange(seen[key])
                            if j < max_quotes_per_category:
                                q[j] = snippet
        total = sum(v for a in per.values() for k, v in a.items() if ":" in k)
        return Result(
            value=total,
            answer="ok",
            explanation=f"{total} lexicon hits over {sum(a['calls'] for a in per.values())} model calls",
            metadata={"lexicon": LEXICON, "per_agent": {k: dict(v) for k, v in per.items()}, "quotes": dict(quotes),
                      "model": transcript.model},
        )

    return scan
