# message_board

Extracts the message board's journal from a `collaboration_index` team run: who messaged whom, when, in reply to what, and which messages each agent received.

## What it measures

One result per run, holding the board's event journal:

- `register`: an agent choosing its board name
- `message`: an agent posting to the global board or a DM, with `reply_to` when the agent marked it as a reply
- `read`: messages delivered to an agent for the first time (`delivered` lists their sequence numbers)

"Delivered" means a read or wait call returned the message to the agent. It does not show the agent acted on it.

## How it works

The harness exports the journal into the sample store inside the solver span, so it is recorded as `StoreEvent`s. The scanner loads only store events (no chat messages), replays their JSON-patch changes, and reads `BoardHistory:journal`. No model is called.

## Output

- `value`: number of messages
- `answer`: `ok`, or `no_journal` if the store has no journal
- `metadata.journal`: compact events with `sequence`, `actor`, `room`, `kind`, `time`, plus `text_len` and `text_sha` (12-char SHA-256 prefix) for messages. Message text is not returned.
- `metadata.peers`: per-agent token counts
- `metadata.call_counts`, `metadata.completed_send_calls`: board tool calls from `BoardHistory:calls`, for cross-checking the journal
- `metadata.scores`: the sample's scores

## Use

Package `collab_message_board`, scanner `board_journal`. See [examples/example.scan.yaml](examples/example.scan.yaml).

Test: `python tests/test_scanner.py`
