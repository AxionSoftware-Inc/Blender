#!/bin/zsh
set -euo pipefail

SOURCE_DIR="/Users/macbookpro/Documents/Blender/spectra_science"
TARGET_ROOT="$HOME/Library/Application Support/Blender/4.5/scripts/addons"
TARGET_DIR="$TARGET_ROOT/spectra_science"

mkdir -p "$TARGET_ROOT"
rm -rf "$TARGET_DIR"
cp -R "$SOURCE_DIR" "$TARGET_DIR"
find "$TARGET_DIR" -name "__pycache__" -type d -prune -exec rm -rf {} +

echo "Installed Spectra Science into:"
echo "$TARGET_DIR"
echo
echo "If Blender is open:"
echo "1. Preferences > Add-ons > disable Spectra Science"
echo "2. enable Spectra Science again"
echo "3. if it still caches old code, restart Blender once"
