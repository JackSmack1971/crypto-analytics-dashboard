
#!/usr/bin/env bash
set -euo pipefail
BACKUPS_DIR="./data/backups"
test -d "$BACKUPS_DIR" || (echo "No backups dir" && exit 1)
echo "Verify stub OK"
