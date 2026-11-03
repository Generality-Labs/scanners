# `affect_keywords_scanner`

Counts emotional language in each agent's reasoning and visible output with a fixed keyword lexicon. No model is
called. Meant as a transparent baseline and a quick check of whether a transcript contains any overt affect.

## Output

One result per transcript. `value` is the total number of lexicon hits.

- `metadata.per_agent[agent]`: `calls`, `reasoning_chars`, `visible_chars`, `redacted_blocks` (reasoning blocks whose
  content was redacted), `summary_only_blocks` (redacted blocks that carried a readable summary, which is counted
  instead), and `<channel>:<category>` hit counts, channel `reasoning` or `visible`.
- `metadata.quotes["<channel>:<category>"]`: up to `max_quotes_per_category` snippets (reservoir sample) of about
  280 characters around hits, with agent and time.
- `metadata.lexicon`: the regexes used.

Reasoning is read from `ContentReasoning` blocks and from `<think>...</think>` inside text. Agents are attributed as in
`activity_scanner`.

## Caveats

Keyword matches include non-affective uses (a function named `annoy`, quoted user text). Read the quotes before
treating counts as emotion.
