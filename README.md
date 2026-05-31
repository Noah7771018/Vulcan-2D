# VULCAN-2D

**V**ariability-aware **U**nified simulator for **L**ayered-material **C**onduction **AN**alysis.

A device-level physical simulator for **2D-material memristors** (h-BN 1T1M), with an
interactive 3D UI. The physics is a validated **non-filamentary soft-breakdown** model
(faithful to Zhu/Lanza, *Nature* 618, 57–62, 2023): the h-BN area is K parallel
sub-populations ("patches") that soft-break progressively, in series with the 1T
transistor (load-line divider). It reproduces the measured I–V loops and their
cycle-to-cycle statistics, and shows the **experiment ↔ simulation** overlay live.

> Fudan University FDUROP 曦源项目. Advisor: 朱凯晨 (Zhu Kaichen). The model is calibrated
> against the group's hybrid 2D/CMOS h-BN 1T1M measurements (`1T1M写入/擦除.xlsx`).

## Architecture

Two processes during development:

```
┌─────────────────────────┐        HTTP /simulate        ┌──────────────────────────┐
│  Python engine           │ ───────────────────────────▶ │  TypeScript + Three.js UI │
│  vulcan2d/  (validated    │   model + measured I-V loops │  (Vite / Electron)        │
│  non-filamentary model)   │ ◀───────────────────────────  │  3D device + I-V plot     │
└─────────────────────────┘                               └──────────────────────────┘
```

The validated physics stays in Python (`vulcan2d/`, where the model research happens); the
UI fetches simulated + measured loops and renders them. (A later step can port the model
into TypeScript for a single double-click desktop binary.)

## Run

Two terminals:

```bash
# 1) physics engine  (needs a Python with numpy/scipy/pandas/openpyxl)
npm run engine            # → http://127.0.0.1:8000   (override interpreter with VULCAN_PY=…)

# 2) UI
npm run dev               # → http://localhost:5173
```

The UI shows "engine ✓" when connected. `npm run electron` packages the desktop window
(point it at a running engine).

## Desktop app (send to others)

Builds a double-click app with the Python engine bundled as a sidecar — recipients
need no Python, Node, or terminal.

```bash
npm run dist:mac     # → release/VULCAN-2D-<ver>-arm64.dmg   (Apple Silicon)
npm run dist:win     # → Windows installer (must be run ON Windows)
```

Pipeline: `scripts/build_engine.sh` (PyInstaller → a numpy-only engine binary, no raw
data inside) → `vite build` → electron-builder (bundles the engine as `extraResources`;
`electron/main.cjs` spawns it on launch and kills it on quit) → `scripts/afterPack.cjs`
ad-hoc code-signs the app (required for Apple Silicon).

Notes for recipients:
- The app is **ad-hoc signed but NOT Apple-notarized** (no paid Developer ID). Any copy
  received via download / WeChat / AirDrop gets a quarantine flag, so the first open shows
  *"Apple cannot verify…"*. To open it (once):
  - **Terminal:** `xattr -dr com.apple.quarantine /Applications/VULCAN-2D.app`, then double-click; **or**
  - **GUI (macOS 15/26):** try to open → click *Done* → **System Settings → Privacy & Security**
    → **Open Anyway** → confirm. (On macOS 15+, the old *right-click → Open* no longer bypasses this.)
  - To remove the prompt entirely, the app must be **Apple-notarized** (paid Developer ID) —
    wire signing+notarization into the build if the group has an account.
- Builds are per-platform: the macOS arm64 `.dmg` won't run on Intel Macs or Windows —
  build those on the respective OS.

## What the simulator does

- **I–V · model vs measured** — the model's SET / RESET median loops (amber) overlaid on
  the measured cell (grey), with a 10–90% variability band. The validation readout below
  shows V_set, V_reset, R_HRS, R_LRS, I_cc and the memory window, model / data.
- **3D device · soft-breakdown patches** — K areal patches that light up progressively as
  φ̄ rises during SET (non-filamentary; **not** a single conductive filament). The patch
  count tracks K; orbit to inspect, adjust h-BN layers.
- **Live controls** — compliance I_cc, sub-populations K, variability σ, MC cycles,
  re-sample. Each re-queries the engine.

## The model (`vulcan2d/`)

See [vulcan2d/README_v0.2.md](vulcan2d/README_v0.2.md) for the physics, the honest
emergent-vs-calibrated split, and the validation table. Reproduce the validation figure:

```bash
npm run engine   # (or:)  $VULCAN_PY -m vulcan2d.validate
```

## Project layout

- `vulcan2d/` — the validated Python model + `serve.py` (engine HTTP server).
- `analysis/` — data exploration, feature extraction, figures.
- `src/` — the TypeScript UI: `engine.ts` (model client), `viz/ivplot.ts` (I–V overlay),
  `viz/device3d.ts` (non-filamentary 3D), `main.ts`.
- See [CLAUDE.md](CLAUDE.md) for the full architecture.
