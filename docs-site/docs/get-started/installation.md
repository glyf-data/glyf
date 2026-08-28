# Installation

`glyf` is published on PyPI as **`glyf-core`**. The package installs the `glyf`
command (and the `glyf` Python module); only the distribution name differs.

Prebuilt wheels are available for:

| OS | Architectures |
| --- | --- |
| Linux | x86_64, aarch64 (manylinux) |
| macOS | Intel, Apple Silicon |
| Windows | x86_64 |

All wheels target Python 3.11 or newer through the stable ABI, so one wheel per
platform covers every supported Python version and no Rust toolchain is needed.

## Recommended: uv

[uv](https://docs.astral.sh/uv/) installs `glyf` into an isolated environment
and puts the command on your `PATH`:

```bash
uv tool install glyf-core
glyf --version
```

If `glyf` is not found afterwards, run `uv tool update-shell` once and open a
new terminal.

## One-line install script

On macOS and Linux, this installs `uv` if it is missing and then installs
`glyf` with it:

```bash
curl -fsSL https://raw.githubusercontent.com/glyf-data/glyf/main/install.sh | sh
```

```bash
# upgrade an existing installation
curl -fsSL https://raw.githubusercontent.com/glyf-data/glyf/main/install.sh | sh -s -- --update

# install an exact version
curl -fsSL https://raw.githubusercontent.com/glyf-data/glyf/main/install.sh | sh -s -- --version 0.3.0
```

The script never uses `sudo`. It installs into uv's tool directory
(`~/.local/bin` by default; override with `GLYF_INSTALL_DIR`) and tells you
what to add to your `PATH` if that directory is not already on it. Pass
`--no-uv-install` to make it fail rather than install `uv` for you, and
`--help` to see every option.

Piping a script into a shell means trusting its source. To read it first:

```bash
curl -fsSL https://raw.githubusercontent.com/glyf-data/glyf/main/install.sh -o install.sh
less install.sh
sh install.sh
```

Windows is not covered by the script; use `uv tool install glyf-core`.

## pipx or pip

```bash
pipx install glyf-core
```

```bash
python -m pip install glyf-core
```

Prefer `uv` or `pipx` for a CLI tool; use `pip` when you want `glyf` inside an
existing project virtual environment, for example next to `dbt-core`.

## Upgrade

```bash
uv tool upgrade glyf-core
# or
pipx upgrade glyf-core
# or
python -m pip install --upgrade glyf-core
```

## Install a specific release

Every [GitHub Release](https://github.com/glyf-data/glyf/releases) ships the
platform wheels, the source distribution, and a `checksums.txt`. For offline or
air-gapped machines, download the wheel for your platform, verify it, and
install from the file:

```bash
sha256sum --check --ignore-missing checksums.txt
uv tool install ./glyf_core-<version>-cp311-abi3-<platform>.whl
```

To pin a version from PyPI instead:

```bash
uv tool install "glyf-core==0.3.0"
```

## Windows

`glyf` ships a native Windows wheel; its dependencies (`duckdb`,
`vl-convert-python`, `pyarrow`) do as well, so PowerShell works without WSL:

```powershell
uv tool install glyf-core
glyf --version
```

Paths in `glyf.yml` and dashboard YAML use forward slashes on every platform.

## Verify

```bash
glyf --version
glyf doctor --project-dir path/to/dbt_project
```

`doctor` reports whether the dbt artifacts, chart files, and DuckDB execution
are ready before your first `glyf build`.

## Next steps

- [Quickstart](quickstart.md) to scaffold a new glyf setup.
- [Existing dbt project](existing-dbt-project.md) to add glyf to a repo you already have.
