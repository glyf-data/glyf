#!/bin/sh
# Install the glyf CLI.
#
#   curl -fsSL https://raw.githubusercontent.com/glyf-data/glyf/main/install.sh | sh
#   curl -fsSL https://raw.githubusercontent.com/glyf-data/glyf/main/install.sh | sh -s -- --update
#   curl -fsSL https://raw.githubusercontent.com/glyf-data/glyf/main/install.sh | sh -s -- --version 0.3.0
#
# glyf is a Python package, so this wraps uv (https://docs.astral.sh/uv/)
# rather than downloading a single binary. Nothing here needs sudo.

set -eu

PACKAGE="glyf-core"
BIN="glyf"
DOCS_URL="https://github.com/glyf-data/glyf"
UV_INSTALLER_URL="https://astral.sh/uv/install.sh"

UPDATE=0
INSTALL_UV=1
VERSION=""

info() {
    echo "$*"
}

warn() {
    echo "Warning: $*" >&2
}

die() {
    echo "Error: $*" >&2
    exit 1
}

usage() {
    cat <<EOF
Install the ${BIN} CLI (PyPI package ${PACKAGE}).

Usage:
  install.sh [options]

Options:
  -u, --update           Upgrade an existing installation to the latest release.
      --version VERSION  Install an exact version, for example 0.3.0.
      --no-uv-install    Fail instead of installing uv when it is missing.
  -h, --help             Show this message.

Environment:
  GLYF_INSTALL_DIR   Directory to place the ${BIN} executable in.
  UV_TOOL_BIN_DIR    Same thing, honoured directly by uv.
EOF
}

while [ $# -gt 0 ]; do
    case "$1" in
        -u | --update)
            UPDATE=1
            ;;
        --version)
            [ $# -ge 2 ] || die "--version requires a value, for example --version 0.3.0"
            VERSION="$2"
            shift
            ;;
        --version=*)
            VERSION="${1#--version=}"
            [ -n "$VERSION" ] || die "--version requires a value, for example --version=0.3.0"
            ;;
        --no-uv-install)
            INSTALL_UV=0
            ;;
        -h | --help)
            usage
            exit 0
            ;;
        *)
            echo "Error: unknown option '$1'" >&2
            echo >&2
            usage >&2
            exit 1
            ;;
    esac
    shift
done

require_command() {
    command -v "$1" >/dev/null 2>&1 ||
        die "required command '$1' is unavailable. Install it and retry."
}

require_command curl

OS=$(uname -s)
ARCH=$(uname -m)

case "$OS" in
    Darwin | Linux) ;;
    MINGW* | MSYS* | CYGWIN* | Windows_NT)
        die "this script targets macOS and Linux. On Windows, install uv from
       https://docs.astral.sh/uv/getting-started/installation/ and run:
         uv tool install ${PACKAGE}"
        ;;
    *)
        die "unsupported operating system: ${OS}. ${PACKAGE} publishes wheels for
       macOS, Linux, and Windows; install it with 'uv tool install ${PACKAGE}'
       or 'pip install ${PACKAGE}'."
        ;;
esac

case "$ARCH" in
    x86_64 | amd64 | arm64 | aarch64) ;;
    *)
        die "unsupported architecture: ${ARCH}. ${PACKAGE} ships wheels for x86_64
       and arm64 only. Building from source needs a Rust toolchain:
         pip install ${PACKAGE}"
        ;;
esac

info "Detected platform: ${OS} / ${ARCH}"

# uv drops its own binary here when installed by the official script.
UV_DEFAULT_BIN="${XDG_BIN_HOME:-$HOME/.local/bin}"

install_uv() {
    info "uv was not found; installing it from ${UV_INSTALLER_URL}"
    curl -LsSf "$UV_INSTALLER_URL" | sh ||
        die "could not install uv. Install it manually from
       https://docs.astral.sh/uv/getting-started/installation/ and retry."

    # The uv installer only edits shell rc files, which do not affect this
    # process, so make the freshly installed uv visible to this script.
    PATH="${UV_DEFAULT_BIN}:${PATH}"
    export PATH

    command -v uv >/dev/null 2>&1 ||
        die "uv was installed but is not on PATH. Open a new shell and rerun this script."
}

if ! command -v uv >/dev/null 2>&1; then
    [ "$INSTALL_UV" -eq 1 ] ||
        die "uv is required but not installed, and --no-uv-install was passed.
       Install uv from https://docs.astral.sh/uv/getting-started/installation/
       and retry."
    install_uv
fi

info "Using uv: $(command -v uv) ($(uv --version 2>/dev/null || echo 'unknown version'))"

if [ -n "${GLYF_INSTALL_DIR:-}" ]; then
    UV_TOOL_BIN_DIR="$GLYF_INSTALL_DIR"
    export UV_TOOL_BIN_DIR
fi

SPEC="$PACKAGE"
[ -n "$VERSION" ] && SPEC="${PACKAGE}==${VERSION}"

if [ -n "$VERSION" ]; then
    # --force so that pinning to a version also works as a downgrade.
    info "Installing ${SPEC}..."
    uv tool install --force "$SPEC" || die "uv could not install ${SPEC}."
elif [ "$UPDATE" -eq 1 ]; then
    info "Upgrading ${PACKAGE}..."
    if ! uv tool upgrade "$PACKAGE"; then
        info "${PACKAGE} was not installed yet; installing it instead."
        uv tool install "$PACKAGE" || die "uv could not install ${PACKAGE}."
    fi
else
    info "Installing ${PACKAGE}..."
    uv tool install "$PACKAGE" || die "uv could not install ${PACKAGE}."
fi

BIN_DIR="${UV_TOOL_BIN_DIR:-$(uv tool dir --bin 2>/dev/null || echo "$UV_DEFAULT_BIN")}"
BIN_PATH="${BIN_DIR}/${BIN}"

[ -x "$BIN_PATH" ] ||
    die "uv reported success but ${BIN_PATH} is missing. Run 'uv tool list' to inspect."

INSTALLED_VERSION=$("$BIN_PATH" --version 2>/dev/null) ||
    die "${BIN_PATH} was installed but did not run. Run '${BIN_PATH} --version' to see why."

info ""
info "${INSTALLED_VERSION} installed to ${BIN_PATH}"

case ":${PATH}:" in
    *":${BIN_DIR}:"*) ;;
    *)
        info ""
        warn "${BIN_DIR} is not on your PATH."
        info "Add it by running 'uv tool update-shell', or add this line to your shell profile:"
        info ""
        info "  export PATH=\"${BIN_DIR}:\$PATH\""
        info ""
        info "Then open a new shell."
        ;;
esac

info ""
info "Next steps:"
info "  ${BIN} init        # scaffold a project"
info "  ${BIN} --help      # see all commands"
info "  ${DOCS_URL}"
