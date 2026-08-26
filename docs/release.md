# Release Process

## Versioning

`glyf` follows semantic versioning:

- patch: bug fixes and docs-only changes
- minor: backwards-compatible features
- major: breaking CLI, config, or artifact contract changes

The version is declared in three places and must match:

- `pyproject.toml` → `[project].version`
- `Cargo.toml` → `[workspace.package].version` (and the `glyf-core` entry in
  `Cargo.lock`)
- `src/glyf/__init__.py` → `__version__`

## Distribution name

The PyPI distribution is **`glyf-core`**. The CLI command is `glyf` and the
Python package is `import glyf`; only the distribution name differs (the bare
`glyf` name on PyPI is held by an unrelated project). Wheels are therefore
named `glyf_core-<version>-cp311-abi3-<platform>.whl`.

## Build Process

From the repository root:

```bash
uv sync
uv run pytest
uv build
```

Build outputs are written to `dist/`. The extension module is built against
the abi3 stable ABI, so one wheel per platform covers Python 3.11+.

## Local Install Test

After building:

```bash
uv tool uninstall glyf-core
uv tool install dist/glyf_core-*.whl
glyf --help
```

If you prefer not to modify the active environment, create a temporary virtual
environment and install the wheel there.

## Publish Process

1. Confirm tests pass:

   ```bash
   task ci
   ```

2. Update `CHANGELOG.md`: rename the `Unreleased` heading to the version and
   date, and confirm the version in `pyproject.toml`, `Cargo.toml`, and
   `src/glyf/__init__.py`.

3. Optional dry run: in GitHub → Actions → **release** → *Run workflow*,
   tick **publish_to_testpypi**. This builds every wheel and the sdist and
   uploads them to https://test.pypi.org/p/glyf-core. Verify with:

   ```bash
   uv tool install --index-url https://test.pypi.org/simple/ \
     --index-strategy unsafe-best-match glyf-core==<version>
   glyf --help
   ```

   TestPyPI uploads are immutable too; re-running with the same version is a
   no-op (`skip-existing`), so bump to a `.devN`/`rcN` version for a second
   dry run.

4. Merge to `main`, then create and push a release tag that matches the
   package version (the workflow refuses a mismatch):

   ```bash
   git tag v0.3.0
   git push origin v0.3.0
   ```

5. `.github/workflows/release.yml` then, in order: checks the tag against the
   version, builds wheels for x86_64/aarch64 Linux, Intel/Apple Silicon macOS,
   and x86_64 Windows plus a source distribution, smoke-tests each wheel with
   `glyf --help`, publishes a GitHub Release with the artifacts and a
   `checksums.txt`, and finally uploads the same files to
   https://pypi.org/p/glyf-core via trusted publishing (OIDC — there are no
   PyPI tokens in the repository secrets).

   Both PyPI jobs use GitHub environments (`pypi`, `testpypi`) that must exist
   in the repository settings and be registered as trusted publishers on
   PyPI / TestPyPI with workflow `release.yml`.

Users then install with:

```bash
uv tool install glyf-core
# or
pip install glyf-core
```

## Release Checklist

- Update `CHANGELOG.md`.
- Bump the version in `pyproject.toml`, `Cargo.toml`, `Cargo.lock`, and
  `src/glyf/__init__.py`.
- Run `task ci`.
- Install the wheel locally and run `glyf --help`.
- Push a `v*` tag and verify the GitHub Release artifacts and the PyPI upload.
