# scanners

[Inspect Scout](https://github.com/meridianlabs-ai/inspect_scout) scanners from Generality Labs, for analysing eval transcripts.

## Layout

Each scanner is its own folder under `scanners/`, installable on its own:

```
scanners/<scanner>/
  README.md               what it measures, what it works on, how, output, use
  pyproject.toml          package metadata and dependencies
  <scanner>/__init__.py   exports the scanner
  <scanner>/scanner.py    the scanner
  tests/test_scanner.py   runs on synthetic input, no real logs needed
  examples/example.scan.yaml   Hawk scan config
```

## Scanners

| Scanner | What it does | Works on | LLM |
|---|---|---|---|
| [message_board](scanners/message_board/) | Extracts who messaged whom, and who received what | `collaboration_index` team runs | No |

## Running a scanner on Hawk

Pin it by commit SHA and subdirectory:

```yaml
scanners:
- package: git+https://github.com/Generality-Labs/scanners@<SHA>#subdirectory=scanners/<scanner>
  name: <scanner>
  items:
  - name: <scanner function>
```

## Adding a scanner

Copy the layout above, keep the README sections, make the test run without real logs, and add a row to the table.
