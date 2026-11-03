# scanners

Inspect Scout scanners from Generality Labs. Each top-level directory is an independently installable package.

| Package | What it does | Uses an LLM |
|---|---|---|
| [`mc_board`](mc_board/) | Extracts the collaboration message-board journal from multi-agent MirrorCode runs | No |

## Using a scanner on Hawk

Pin the package by commit SHA and subdirectory in the scan config:

```yaml
scanners:
- package: git+https://github.com/Generality-Labs/scanners@<SHA>#subdirectory=mc_board
  name: mc_board
  items:
  - name: board_journal
```

Each package has an `examples/` config and `tests/`.
