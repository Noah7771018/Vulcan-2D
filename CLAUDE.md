# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Status: integrated simulator running (Python engine + TS UI)

VULCAN-2D is a Fudan University undergraduate research project (FDUROP 曦源项目). A
**preliminary complete simulator runs**: the validated Python model (`vulcan2d/`) serves
I–V loops over HTTP to the TypeScript/Three.js UI, which shows a **model-vs-measured I–V
overlay** + validation readout and a **non-filamentary 3D device** (areal soft-breakdown
patches lighting up with φ̄). See "App: stack & how to run".

Division of labor (important): **the student team does the physics-model research (in
Python, `vulcan2d/`); Claude writes and maintains all the UI/integration code.** Optimize
technical choices for performance and visual quality, not for student-maintainability.

PHYSICS NOTE — the device is **non-filamentary** (h-BN soft-breakdown, K areal patches in
series with the 1T transistor; faithful to Zhu/Lanza *Nature* 2023). Do **not** depict a
single conductive filament — that was an early wrong picture, now corrected.

The chosen integration is "Python engine first" (UI calls a local server); a later step can
port the model into TypeScript for a single double-click desktop binary. What remains:
expose the new `p_perc` percolation knob / endurance hooks in the UI if wanted; package the
engine as a sidecar (PyInstaller) for a one-click desktop build; optionally port to TS.

Current contents of the workspace:

- `1-2.【立项】曦源项目申请书（2026年版）v3(1).docx` — the project proposal / 开题报告. This is
  the authoritative spec for what VULCAN-2D should be. Re-read it (extract text from the
  zipped `word/document.xml`) when scope or physics details are unclear.
- `1T1M写入.xlsx`, `1T1M擦除.xlsx` — experimental I–V data for model calibration/validation
  (see "Experimental data" below).
- `比较2.opju` — an OriginLab project file (binary) used for plotting the measured data.
- `微信图片_*.jpg` — a reference image (h-BN memristor 1R vs. 1T1M I–V comparison).

This workspace **is a git repository** (`main` branch, no commits yet). A `.gitignore`
**excludes the unpublished experimental data (`*.xlsx`, `*.opju`) and the proposal
(`*.docx`, which carries personal info)** from version control — these stay local. If the
repo is kept *private* and you want the data versioned, override those lines (consider
git-lfs for the large `.xlsx`/`.opju`). Code, docs, and `CLAUDE.md` are tracked normally.

## Who's who (advisor)

The **actual advisor is 朱凯晨 (Zhu Kaichen)** — Young Researcher at Fudan's School of
Future Information / Institute of Optoelectronics (`zhukaichen@fudan.edu.cn`). His group's
2D-memristor / memristive-CMOS integration work is the experimental basis of this project.

Note on the proposal text: 王水源 (Wang Shuiyuan) appears as advisor in an *earlier* draft
(v4), but that was only a nominal/placeholder listing to file the application. The current
docx (v3) and the real supervision are **朱凯晨's**. Treat 朱凯晨 as the advisor in any
context, attribution, or correspondence.

## App: stack & how to run

Two processes (dev): a **Python physics engine** + a **TypeScript/Three.js UI**.

- **Engine** — `vulcan2d/serve.py` wraps the validated model in a stdlib HTTP server
  (no extra Python deps). `GET /simulate?icc_ua=&K=&sigma=&ncycles=&seed=&vset=` runs an
  N-cycle MC and returns model SET/RESET median loops, the **measured** loops (from the
  xlsx, for the overlay), the φ̄(V) trajectory, and features vs data targets.
- **UI** — TypeScript + Three.js (WebGL2) + Vite, Electron for desktop. Chosen because the
  dev machine is **Apple M4 / Metal**: WebGL runs native-class through Metal, while
  OpenGL-based stacks (Julia GLMakie / Python VTK) are the weakest 3D path on this hardware.

```
npm install
npm run engine     # Python model server → http://127.0.0.1:8000
                   #   (override the interpreter: VULCAN_PY=/path/to/python npm run engine;
                   #    needs numpy/scipy/pandas/openpyxl — the miniforge `d2l` env has them)
npm run dev        # Vite UI → http://localhost:5173   (shows "engine ✓" when connected)
npm run build      # tsc --noEmit + vite build → dist/  (must stay green)
npm run electron   # desktop window (point at a running engine)
```

Layout:
- `vulcan2d/` — **the validated Python model** (the team's research lands here): `model.py`
  (non-filamentary soft-breakdown + load-line divider + kinetics), `features.py`,
  `calibrate.py`, `validate.py`, `serve.py` (engine), `vulcan2d_calibrated.npz`. Verify with
  `$VULCAN_PY -m vulcan2d.validate`. The UI must NOT re-implement physics — it calls this.
- `analysis/` — data exploration, feature CSVs, figures (incl. `figures/09_*` validation).
- `src/engine.ts` — typed client for the engine (`simulate(params)`).
- `src/viz/ivplot.ts` — Canvas-2D model-vs-measured I–V overlay (clean, legible — NOT a
  cloud of curves); `src/viz/device3d.ts` — the non-filamentary 3D (areal patches,
  Three.js). Glow uses unlit basic materials + additive sprites, **no HDR bloom**
  (UnrealBloomPass produced a magenta artifact under software-GL; verify visuals on the
  real Metal GPU, e.g. headed Chrome `channel:'chrome'`, not headless SwiftShader).
- `src/main.ts` — fetch-from-engine wiring + render loop. `electron/main.cjs` — desktop shell.

The old TS phenomenological physics (`src/physics/`, QPC/Poole-Frenkel filament) was
**deleted** — superseded by the Python model. Do not reintroduce a second physics.

## What VULCAN-2D is

VULCAN = **V**ariability-aware **U**nified simulator for **L**ayered-material **C**onduction
**AN**alysis. It is a device-level **physical simulator for 2D-material memristors** (RRAM
built from layered materials such as h-BN, graphene, TMDs), filling a gap left by existing
physical simulators (e.g. SIM²RRAM) that target HfO₂-class oxide RRAM.

Goal: reproduce, quantitatively, a device's **I–V characteristics** and **set/reset
switching behavior**, including **device-to-device and cycle-to-cycle variability**, then
calibrate/validate against the advisor group's real 2D-memristor measurements to form an
"experiment ↔ simulation" closed loop.

**SIM²RRAM is the architectural reference model** — the project's plan is to mirror its
solver structure (coupled kinetic / thermal / transport equations) and then swap in
physics specific to 2D layered materials. When in doubt about overall structure, consult
the SIM²RRAM paper (Villena et al., *J. Comput. Electron.* 2017, ref [1] in the proposal).

## Planned simulator architecture (the physics modules to build)

The proposal specifies four coupled physical models. Treat these as the module breakdown:

1. **Conductive filament formation / rupture** — filament geometry + defect (vacancy)
   dynamics governing the set/reset transitions.
2. **Charge transport** — regime-dependent conduction:
   - Low-resistance state (LRS): **Quantum Point Contact (QPC)** model (quantized
     conductance through the filament).
   - High-resistance state (HRS): **Poole–Frenkel** (and similar trap-assisted) emission.
3. **Joule heating / temperature field** — local temperature drives the thermally
   activated reset; electro-thermal coupling.
4. **Device variability** — statistical modeling of parameter spread so simulated I–V and
   set/reset distributions match measured variability. The advisor group's
   two-dimensional variability-coefficient method (ref [4]) is the intended analysis lens.

These are **multiphysics-coupled** (electrical ↔ thermal ↔ defect). Numerical stability
and convergence of the coupled solve is called out in the proposal as a primary
difficulty — expect this to need care, not a naive fixed-point loop.

**Implementation language:** the proposal names **Python or MATLAB**. No choice is locked
in; if starting the codebase, confirm with the user which to use before scaffolding.

## Experimental data (calibration / validation targets)

These are real measurements from advisor **朱凯晨's group's work on hybrid 2D/CMOS
memristive microchips** (cf. K. Zhu et al., "Hybrid 2D/CMOS microchips for memristive
applications," *Nature* 618, 57–62, 2023). The 1T1M structure = an h-BN memristor in series
with a CMOS transistor that provides compliance/current-limiting (the red, narrowed I–V in
the reference image; the bare 1R memristor is the wide, variable blue I–V). Notably the
corresponding author and co-authors of that Nature paper (Lanza, Villena, Roldán) are also
the authors of SIM²RRAM — the simulator this project takes as its architectural reference.

`1T1M写入.xlsx` (write) and `1T1M擦除.xlsx` (erase) hold measured I–V curves from a 1T1M
(one-transistor–one-memristor) cell:

- Each file has **53 worksheets** (one per cycle/measurement run).
- Each sheet has columns headed `voltage` and `current` (write sheets carry a third
  column). Write sheets run ~500 rows; erase sheets ~170 rows.

These are the ground truth the simulator's I–V and set/reset output must reproduce.
Reading them programmatically: they are standard `.xlsx`, so `pandas.read_excel(path,
sheet_name=None)` (Python) loads all 53 sheets as a dict. `.opju` is OriginLab's binary
format and is not readable without Origin — use the `.xlsx` files as the data source for
any code.

## Working notes

- The project is bilingual: the proposal and filenames are Chinese; code and docs can be
  English. Preserve the Chinese filenames as-is (they are referenced elsewhere).
- The 12-month plan (from the proposal): months 1–2 literature/framework; 3–5 core physics
  modules (filament, QPC transport, thermal); 6–8 add variability + initial calibration;
  9–10 validation/optimization + variability analysis; 11–12 report + docs. Use this to
  judge what stage a request belongs to.
- Deliverable is "runnable simulator + source + usage docs" reproducing measured I–V,
  HRS/LRS, and set/reset behavior. Quantitative agreement with the `.xlsx` data is the bar.
