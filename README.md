# gl-scanners

[Inspect Scout](https://github.com/meridianlabs-ai/inspect_scout) scanners from Generality Labs.

| Scanner | What it does | LLM | Docs |
|---|---|---|---|
| `message_board_scanner` | Who messaged whom, and who received what, in multi-agent team runs | No | [docs/message_board.md](docs/message_board.md) |

## Using on Hawk

Pin a release tag:

```yaml
scanners:
- package: git+https://github.com/Generality-Labs/scanners@v0.1.0
  name: gl_scanners
  items:
  - name: message_board_scanner
```

## Adding a scanner

Add `src/gl_scanners/<name>.py`, export it from `_registry.py`, write `docs/<name>.md`, add a row to the table above and a test in `tests/` that runs on synthetic transcripts.

## Releasing

Any change to `src/` or `pyproject.toml` bumps the version in both `pyproject.toml` and `src/gl_scanners/version.py`, then tags it:

```bash
git tag v<version> && git push origin v<version>
```

Change a scanner's `version=` in its `@scanner` decorator when its output changes, so Scout re-scans transcripts it has already done.
