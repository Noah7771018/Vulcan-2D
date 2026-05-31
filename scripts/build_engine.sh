#!/usr/bin/env bash
# Build the VULCAN-2D Python engine into a standalone (numpy-only) binary that
# the Electron app bundles as a sidecar. Requires a Python with numpy +
# PyInstaller (override via VULCAN_PY). The measured-overlay JSON is precomputed
# first so the shipped engine needs neither pandas nor the raw xlsx.
set -euo pipefail
PY="${VULCAN_PY:-/opt/homebrew/Caskroom/miniforge/base/envs/d2l/bin/python}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "[1/2] precompute measured overlay → vulcan2d/measured_loops.json"
"$PY" -m vulcan2d.precompute_measured

echo "[2/2] PyInstaller → engine-dist/vulcan-engine"
"$PY" -m PyInstaller --onedir --name vulcan-engine --noconfirm \
  --distpath engine-dist --workpath engine-build --specpath engine-build \
  --paths "$ROOT" \
  --add-data "$ROOT/vulcan2d/vulcan2d_calibrated.npz:vulcan2d" \
  --add-data "$ROOT/vulcan2d/measured_loops.json:vulcan2d" \
  --exclude-module pandas --exclude-module openpyxl --exclude-module matplotlib \
  --exclude-module scipy --exclude-module PIL --exclude-module tkinter --exclude-module IPython \
  "$ROOT/engine_entry.py"

echo "done → engine-dist/vulcan-engine/vulcan-engine"
