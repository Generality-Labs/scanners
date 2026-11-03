# gl-scanners

[Inspect Scout](https://github.com/meridianlabs-ai/inspect_scout) scanners from Generality Labs.

| Scanner | What it does | LLM | Docs |
|---|---|---|---|
| `communication_scanner` | Who messaged whom, and who read what, in multi-agent runs, as Inspect `CommunicationEvent`s | No | [docs/communication.md](docs/communication.md) |
| `activity_scanner` | Each agent's model calls: output and reasoning tokens, and the tool calls they made | No | [docs/activity.md](docs/activity.md) |

## Using on Hawk

Pin a release tag:

```yaml
scanners:
- package: git+https://github.com/Generality-Labs/scanners@v0.3.0
  name: gl_scanners
  items:
  - name: communication_scanner
```

## Adding a scanner

Add `src/gl_scanners/<name>.py`, export it from `_registry.py`, write `docs/<name>.md`, add a row to the table above and a test in `tests/` that runs on synthetic transcripts.

## Testing

Hawk's runner uses METR's forks of Inspect and Scout, which can be older than PyPI. Run the tests against the versions the runner installs (its log prints them), not just the latest:

```bash
uv venv .venv-hawk && uv pip install --python .venv-hawk/bin/python jsonpatch \
  "inspect-ai @ git+https://github.com/METR/inspect_ai.git@<sha>" \
  "inspect-scout @ git+https://github.com/METR/inspect_scout.git@<sha>"
.venv-hawk/bin/python tests/test_communication.py
.venv-hawk/bin/python tests/test_activity.py
```

## Releasing

Any change to `src/` or `pyproject.toml` bumps the version in both `pyproject.toml` and `src/gl_scanners/version.py`, then tags it:

```bash
git tag v<version> && git push origin v<version>
```

Change a scanner's `version=` in its `@scanner` decorator when its output changes, so Scout re-scans transcripts it has already done.
