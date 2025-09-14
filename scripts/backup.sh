
#!/usr/bin/env bash
set -euo pipefail
DEST="${1:-./data/backups/$(date +%F)}"
mkdir -p "$DEST/sqlite" "$DEST/parquet"
echo "{}" > "$DEST/manifest.json"
echo "Backup stub -> $DEST"
