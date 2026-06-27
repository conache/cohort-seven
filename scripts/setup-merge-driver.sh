#!/usr/bin/env bash
set -euo pipefail

git config merge.devupdates.name "Semantic merge for development-updates.md"
git config merge.devupdates.driver "python3 scripts/dev_updates.py merge %O %A %B"

echo "devupdates merge driver active. Format with: python3 scripts/dev_updates.py format development-updates.md"
