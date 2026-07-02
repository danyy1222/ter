# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Asphalt-TEG Simulator: a desktop app that visualizes and calculates the output of a
thermoelectric generator (TEG) embedded in asphalt, based on the equations and field-test
data from a paper (Tahami et al. 2019). It has three parts:

- `backend/` — FastAPI service that exposes the thermoelectric physics/economics calculations
  as a REST API.
- `ui/index.html` — a single self-contained HTML/CSS/JS file (no build step, no framework)
  that renders a day/night sky animation and live stat panels, polling the backend for
  calculated values.
- `main.py` — a pywebview launcher that opens `ui/index.html` in a native desktop window.

There is no package.json, bundler, or test suite in this repo; everything is plain
Python + a single static HTML file.

## Running the app

Install backend dependencies (from `backend/`, using `py` on Windows or `python3` elsewhere):

```
cd backend
py -m pip install -r requirements.txt
```

Run the API server — must be launched with `backend/` as the working directory, because
`backend/main.py` imports with bare module paths (`from data.temperature_data import ...`,
`from models import ...`, `from teg_engine import ...`) rather than `backend.`-prefixed imports:

```
cd backend
py main.py
```

This starts uvicorn on `http://localhost:8000` (hardcoded `BACKEND` constant in
`ui/index.html`). Equivalently: `cd backend && py -m uvicorn main:app --reload`.

Open the UI directly in a browser (`ui/index.html`) once the backend is running, or launch
the desktop window from the repo root:

```
py -m pip install pywebview
py main.py
```

There are no lint, test, or build commands configured in this repo.

## Architecture

### Backend calculation pipeline (`backend/teg_engine.py`)

All physics/economics live in one module as pure functions, composed into `build_*()`
functions that each return a `{inputs, resultados, formulas_aplicadas, fuente}` dict — this
shape is what every API endpoint returns (validated by `GenericApiResponse` in
`backend/models.py`). When adding a new calculation, follow this same
inputs/resultados/formulas_aplicadas/fuente convention so the frontend's generic renderers
keep working.

Core equation chain (paper equations 1-4), all driven by `build_calculation()`:
1. `calculate_voltage` — Seebeck voltage: `V = alpha * (T_h - T_c)`
2. `calculate_current` — `I = V / (R_int + R_L)`
3. `calculate_power` — `P = I^2 * R_L`
4. `calculate_heat` — heat balance at the hot junction
5. `calculate_copper_flux` — Fourier conduction through the copper plate
6. `calculate_efficiency` — `eta = P / Q * 100`

Higher-level builders compose these: `build_hour_simulation` (single hour from the paper's
temperature table), `build_day_simulation` (10:00-19:00, extrapolating 17:00-19:00 linearly
via `extend_day_hours()` since the source paper only measured up to 16:00),
`build_road_scaling` (extrapolates prototype power density to a road section area),
`build_viability` (LCOE/annualized cost economics), `build_compare_configurations`
(Z-shape vs L-shape prototype geometries, modeled as a flat `+8C` T_h offset per the paper's
note — not independently derived), `build_max_density`.

Physical/economic constants (ALPHA, R_INT, R_LOAD, K_TEG, K_COPPER, plate dimensions,
P_MAX_FIELD, P_AVE_FIELD, COST_UNIT, DISCOUNT_RATE, etc.) are all module-level in
`teg_engine.py` and re-exported through `backend/main.py`'s `/` health-check endpoint.

Real measured data (hourly temperature table + field-test results) lives in
`backend/data/temperature_data.py` and is treated as ground truth; anything outside the
10:00-16:00 measured window is explicitly labeled `"estimado"` / extrapolated rather than
presented as measured.

### API layer (`backend/main.py`, `backend/models.py`)

Thin FastAPI route handlers — each endpoint validates via a Pydantic request model
(`extra="forbid"`, whitespace-stripped) then delegates straight to a `teg_engine.build_*()`
function. CORS is wide open (`allow_origins=["*"]`) since this is a local desktop app talking
to localhost. Endpoints: `/calcular`, `/simular-hora`, `/simular-dia-completo`,
`/temperaturas`, `/escalar-carretera`, `/viabilidad`, `/comparar-configuraciones`,
`/maxima-densidad-potencia`.

### Frontend (`ui/index.html`)

Single file, no dependencies. Key behavior to know before editing:

- **Backend is optional, not required.** `calcularLocal()` reimplements the equation-1-4
  chain in JS as a fallback. `fetchFromBackend()` tries the real API first and falls back to
  the local JS calc on any fetch failure (backend down, CORS, non-2xx) — always keep these
  two implementations in sync when changing the physics.
  `setBackendStatus()`/`#backendStatus` reflects which mode is active.
- The time slider (`#timeSlider`, 0-24h step 0.1) drives everything: sky animation position
  (`updateSky`), day/night phase text, and triggers `fetchFromBackend`/`calcularLocal` for the
  current hour. Hours outside 10:00-19:00 are treated as "no sun" (zeroed output) even though
  `dayMeta()`/night-sky rendering uses a wider 7:00-19:00 window for visuals.
  `interpolateTh(hour)` does client-side linear interpolation over a small hardcoded
  temperature table (`tablaTemp`) mirroring the paper data, separate from the backend's own
  interpolation logic.
- Images (`assets/asfalto.png`, `assets/cobre.png`, `assets/sol.png`) are loaded with a
  cascading fallback path list in `fixImagePaths()` (`./assets/`, `./ui/assets/`, `assets/`,
  `../assets/`) so the same file works whether opened directly, served from repo root, or
  loaded inside the pywebview window. The root-level `imagenes/` directory holds identical
  copies of these same three PNGs (kept as originals/backup — `ui/assets/` is what's actually
  referenced at runtime).
- `drawChart()` and `drawNightSky()` are hand-rolled canvas renderers (no charting library).

### Desktop launcher (`main.py`)

Minimal pywebview wrapper. It does not start the backend — the FastAPI server must be
running separately (see "Running the app" above) for live data; otherwise the window falls
back to `calcularLocal()`.
