# `communication_scanner`

Who communicated with whom in a multi-agent run: every message sent, who it reached, what it replied to, and which messages each agent read. No model is called.

## Output format

Records are in the shape of Inspect's `CommunicationEvent`, the record [inspect_swarm](https://github.com/meridianlabs-ai/inspect_swarm) writes natively, whatever the source:

- `sent`: `agent` is the sender. `send.record` has `id`, `to` (addresses as written, `["all"]` for a broadcast), `recipients` (who that resolved to) and `reply_to`.
- `delivered`: `delivery.recipients` and `delivery.seq` (commit order).
- `read`: `agent` is the reader. `record_ids` are the messages it was shown.

Message text is not in the result: `send.record.content` is `null`, and `data` holds `content_len` and `content_sha` (12-character SHA-256 prefix).

Scout also saves each scanner's input in the results file (the `input` column). Here that is the sample's store events, which include the board journal with message text. Scout's readers skip `input` by default; read only the columns you need rather than downloading the whole parquet.

The result:

- `value`: number of `sent` records
- `answer`: `ok`, or `no_records` if no source matched
- `metadata.source`: where the records came from
- `metadata.roster`: every agent's id and chosen name
- `metadata.events`: the `CommunicationEvent`s, in order
- `metadata.checks`: counts for checking the conversion against the harness's own accounting
- `metadata.score`: the sample's score

## Sources

### collaboration_index

Team runs from the [collaboration_index](https://github.com/pabloRom2004/collaboration-index) harness, on any of its tasks. The harness runs its own message board and saves the board's journal to the sample store (`BoardHistory:journal`). The scanner loads only `StoreEvent`s, replays them to rebuild the store, and converts the journal (`gl_scanners/adapters/collaboration_index.py`):

- Each message becomes `sent` and `delivered`, both at the message's time, since the board commits and publishes a message in one step.
- Global posts are addressed to `all` and reach every other agent on the team. DMs reach the other member of the room.
- Each read becomes `read`, listing the messages returned to that agent for the first time. Being returned by a read does not show the agent acted on a message.

The journal does not record refused sends, waits, or reads that returned nothing new, so those are absent.

`checks.sent` should equal `checks.completed_send_calls`, the harness's own count of successful sends.

### inspect_swarm (not yet)

inspect_swarm writes `CommunicationEvent`s itself. Scout's events filter does not accept `"communication"` yet (inspect-scout 0.6.2, and main as of 2026-11-03), so the scanner cannot load them without loading every event in the log. It will read them directly once Scout can.

## Adding a source

Write an adapter in `gl_scanners/adapters/` with a `SOURCE` name and a `convert(store)` that returns `{"roster", "events", "checks"}`, or `None` when the store is not from its harness, and add it to `ADAPTERS` in `communication.py`.
