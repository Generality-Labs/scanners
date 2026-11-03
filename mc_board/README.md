# mc_board

Extracts the message-board journal from `collaboration_index/mirrorcode` team runs, with no model calls.

The harness exports the board's event journal into the sample store (`BoardHistory:journal`). The scanner reads only `StoreEvent`s, replays them as JSON patches, and returns a compact journal:

- `register`: actor, name
- `message`: actor, room (`global` or a DM room), time, `reply_to`, text length and a 12-char SHA-256 prefix (text is not returned)
- `read`: actor, room, time, `delivered` (message sequences delivered to this actor for the first time)

`Result.value` is the message count. `Result.metadata` also carries team peers' token counts, board call counts by action, and the sample's scores, for cross-checking. `answer` is `no_journal` when the store has no journal.

Test: `python tests/test_board.py`
