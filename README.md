# scanners

[Inspect Scout](https://github.com/meridianlabs-ai/inspect_scout) scanners from Generality Labs, for analysing eval transcripts.

## Layout

```
scanners/
  <group>/              the eval, harness or theme the scanners target
    README.md           what the group covers
    <scanner>/          one installable package per scanner
      README.md         what it measures, how, output, whether it uses an LLM
      pyproject.toml
      <package>/        code
      tests/
      examples/         example Hawk scan config
```

## Scanners

| Group | Scanner | What it does | LLM |
|---|---|---|---|
| [collaboration_index](scanners/collaboration_index/) | [message_board](scanners/collaboration_index/message_board/) | Extracts who messaged whom, and who received what, from multi-agent team runs | No |

## Running a scanner on Hawk

Pin the scanner by commit SHA and subdirectory:

```yaml
scanners:
- package: git+https://github.com/Generality-Labs/scanners@<SHA>#subdirectory=scanners/<group>/<scanner>
  name: <package>
  items:
  - name: <scanner function>
```

Each scanner's `examples/` has a full config.

## Adding a scanner

Put it in the group it belongs to (or start a new group with its own README), copy the README sections of an existing scanner, add a test that runs without real logs, and add a row to the table above.
