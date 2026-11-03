# gl-scanners

[Inspect Scout](https://github.com/meridianlabs-ai/inspect_scout) scanners from Generality Labs.

| Scanner | What it does | LLM |
|---|---|---|
| [`message_board_scanner`](#message_board_scanner) | Who messaged whom, and who received what, in multi-agent team runs | No |

## Using on Hawk

```yaml
scanners:
- package: git+https://github.com/Generality-Labs/scanners@<SHA>
  name: gl_scanners
  items:
  - name: message_board_scanner
```

## Scanners

### `message_board_scanner`

Extracts the message board's journal from a multi-agent team run: who messaged whom, when, in reply to what, and which messages each agent received.

**Works on:** team runs from the [`collaboration_index`](https://github.com/pabloRom2004/collaboration-index) harness, on any of its tasks. It reads that harness's own board records, so it does not work on other multi-agent harnesses.

**How it works:** the harness saves the board's event journal to the sample store (`BoardHistory:journal`), which is recorded as `StoreEvent`s. The scanner loads only store events, replays their JSON-patch changes and reads the journal. No model is called and no chat messages are loaded.

**Output:** one result per run.

- `value`: number of messages
- `answer`: `ok`, or `no_journal` if the store has no journal
- `metadata.journal`: one row per board event, with `sequence`, `actor`, `room` (`global` or a DM room), `kind`, `time`
  - `register` rows add `name`
  - `message` rows add `reply_to`, `text_len` and `text_sha` (12-character SHA-256 prefix); message text is not returned
  - `read` rows add `delivered`: the messages delivered to that agent for the first time. Delivered means a read or wait call returned the message, not that the agent acted on it.
- `metadata.peers`: per-agent token counts
- `metadata.call_counts`, `metadata.completed_send_calls`: board tool calls, for cross-checking the journal
- `metadata.scores`: the sample's scores

## Adding a scanner

Add `src/gl_scanners/<name>.py`, export it from `_registry.py`, add a section above and a row to the table. Tests in `tests/` run on synthetic transcripts, no real logs needed.
