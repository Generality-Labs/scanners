import asyncio, sys
sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else __import__("os").path.dirname(__import__("os").path.dirname(__import__("os").path.abspath(__file__))))
from inspect_ai.event import StoreEvent
from inspect_ai._util.json import JsonChange
from inspect_scout import Transcript
from message_board.scanner import board_journal

J = [
 {"run":"r","sequence":1,"actor":"a1","room":None,"kind":"register","data":{"name":"Ada"},"time":"t1"},
 {"run":"r","sequence":2,"actor":"a1","room":"global","kind":"message","data":{"text":"hello team","reply_to":None,"conversation_kind":"global"},"time":"t2"},
 {"run":"r","sequence":3,"actor":"a2","room":"global","kind":"read","data":{"after":0,"next_after":2,"delivered":[2]},"time":"t3"},
 {"run":"r","sequence":4,"actor":"a2","room":"global","kind":"message","data":{"text":"hi","reply_to":2,"conversation_kind":"global"},"time":"t4"},
]
evs = [
 StoreEvent(changes=[JsonChange(op="add", path="/TeamHistory:peers", value=[{"id":"a1","tokens":5},{"id":"a2","tokens":7}])]),
 StoreEvent(changes=[JsonChange(op="add", path="/BoardHistory:calls", value=[{"request_id":"x","action":"send","completed":True}])]),
 StoreEvent(changes=[JsonChange(op="add", path="/BoardHistory:calls/-", value={"request_id":"y","action":"send","completed":True}),
                     JsonChange(op="add", path="/BoardHistory:journal", value=J)]),
]
t = Transcript(transcript_id="t", source_type="eval_log", source_id="s", source_uri="u", metadata={}, events=evs)
r = asyncio.run(board_journal()(t))
print(r.answer, r.value, r.explanation)
print(r.metadata["journal"]); print(r.metadata["peers"], r.metadata["completed_send_calls"], r.metadata["patch_failures"])
t2 = Transcript(transcript_id="t", source_type="eval_log", source_id="s", source_uri="u", metadata={}, events=evs[:1])
r2 = asyncio.run(board_journal()(t2)); print(r2.answer, r2.explanation)
