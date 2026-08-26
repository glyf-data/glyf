# Release Process

## Versioning

Use semantic versioning once the public API stabilizes:

- patch: bug fixes and docs-only changes
- minor: backwards-compatible features
- major: breaking CLI, config, or artifact contract changes

## Build Process

From the repository root:

```bash
uv sync
uv run pytest
uv build
```

Build outputs are written to:

```text
dist/
```

## Local Install Test

After building:

```bash
uv tool uninstall glyf
uv tool install dist/glyf-*.whl
glyf --help
```

If you prefer not to modify the active environment, create a temporary virtual
environment and install the wheel there.

## Publish Process

The recommended release channel is GitHub Releases with attached wheel files.

1. Confirm tests pass:

   ```bash
   uv run pytest
   ```

2. Build distributions:

   ```bash
   uv build
   ```

3. Inspect `dist/`.

4. Update `CHANGELOG.md` and confirm the package version in `pyproject.toml`.

5. Create and push a release tag:

   ```bash
   git tag v0.2.0
   git push origin v0.2.0
   ```

6. Wait for the GitHub Actions release workflow to build wheels and publish a
   GitHub Release with the generated artifacts.

Users can then install `glyf` directly from a GitHub Release wheel:

```bash
uv tool install \
  https://github.com/glyf-data/glyf/releases/download/v0.2.0/glyf-0.2.0-<platform>.whl
```

The release workflow lives in:

```text
.github/workflows/release.yml
```

PyPI publishing is intentionally deferred.

## Release Checklist

- Update `CHANGELOG.md`.
- Confirm `pyproject.toml` metadata.
- Run `uv run pytest`.
- Run `uv build`.
- Install the wheel locally and run `glyf --help`.
- Push a `v*` tag and verify the GitHub Release artifacts.
