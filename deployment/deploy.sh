#!/usr/bin/env bash
# One-shot deploy: assumes Jenkins/CI has already synced this repo's latest
# main (module code + deployment/) onto this VM. This script clones/updates
# the other 3 addon repos, then (re)starts the stack.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

"$DIR/clone.sh"

cd "$DIR"
docker compose pull db nginx
docker compose up -d --build

echo "Deployed. Endpoints:"
echo "  http://<host>/HRattendance/"
echo "  http://<host>/timesheet/"
echo "  http://<host>/purchaseworkflow/"
echo "  http://<host>/HRexpense/"
