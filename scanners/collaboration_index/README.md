# collaboration_index

Scanners for transcripts from the `collaboration_index` harness: teams of agents sharing one sandbox and a message board, on tasks such as MirrorCode, splitting a fixed token budget across the team.

Each run is one sample with every agent as a separate agent span. The harness saves its own records to the sample store, including the board journal (`BoardHistory`) and team accounting (`TeamHistory`). Scanners here read those records where possible rather than the agents' chat histories.

| Scanner | What it does | LLM |
|---|---|---|
| [message_board](message_board/) | Extracts the board journal: names, messages, replies, deliveries | No |
