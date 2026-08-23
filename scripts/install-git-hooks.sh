#!/usr/bin/env bash
set -euo pipefail

# Installs the repository git hooks into the local clone, so commit messages
# are validated before a pull request reaches CI.
#
# Usage: scripts/install-git-hooks.sh

repo_root="$(git rev-parse --show-toplevel)"
hooks_dir="$(git rev-parse --git-path hooks)"

mkdir -p "$hooks_dir"
cat > "$hooks_dir/commit-msg" <<'HOOK'
#!/usr/bin/env bash
exec "$(git rev-parse --show-toplevel)/scripts/check-commit-message.sh" "$1"
HOOK
chmod +x "$hooks_dir/commit-msg"

echo "Installed commit-msg hook in ${hooks_dir#"$repo_root"/}"
