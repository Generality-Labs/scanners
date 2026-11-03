# `activity_scanner`

What each agent in a multi-agent run spent its model output on, call by call. No model is called.

## Output

One result per run. `metadata.turns` has one row per model call, in order:

| Column | Meaning |
|---|---|
| `agent` | the outermost agent span the call ran in (the team member); `null` if none |
| `time` | the call's timestamp |
| `output_tokens`, `reasoning_tokens`, `input_tokens` | the call's usage as reported by the provider |
| `text_chars` | characters of visible text in the output |
| `reasoning_chars` | characters of readable reasoning (0 when the provider hides it) |
| `tool_calls` | `[function, arg_chars, op, head]` per tool call |

For each tool call, `arg_chars` is the length of its JSON arguments. `op` is a short `command` or `action` argument if it has one (e.g. a message-board `send`). `head` is the first 60 characters of a shell or code argument, enough to tell writing a file from running tests. No other text is returned.

`metadata.unattributed` counts model calls outside any agent span.

## Works on

Any Inspect transcript where agents run in agent spans (`span_begin` events of type `agent`), including `collaboration_index` team runs, where each team member's span is named after its board ID.

## Caveats

- Reasoning tokens are counted by the provider and cannot be split between the tool calls of one turn.
- Model events are loaded in full by Scout. Check the runner's memory on the largest transcript first.
