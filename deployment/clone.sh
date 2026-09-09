#!/usr/bin/env bash
# Clone/update the OTHER 3 addon repos to latest main.
# odoo-hr-attendance itself is not cloned here — this script lives inside
# that repo already, so its own checkout (repo root, one level up) is used
# directly as the addons source for that service.
set -euo pipefail

ORG="SystangoTechnologies"
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/addons"

REPOS=(
  "odoo-timesheet"
  "odoo-purchase-workflow"
  "odoo-hr-expense"
)

mkdir -p "$BASE_DIR"

for repo in "${REPOS[@]}"; do
  target="$BASE_DIR/$repo"
  url="https://github.com/${ORG}/${repo}.git"
  if [ -d "$target/.git" ]; then
    echo "Updating $repo..."
    git -C "$target" fetch origin main
    git -C "$target" checkout main
    git -C "$target" reset --hard origin/main
  else
    echo "Cloning $repo..."
    git clone --branch main --single-branch "$url" "$target"
  fi
done

echo "All addon repos cloned/updated under $BASE_DIR"
echo "odoo-hr-attendance is served from the repo checkout itself (../)"
