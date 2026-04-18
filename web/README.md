# DeepMiro Web Viewer

Vue 3 + Vite + TypeScript realtime viewer for DeepMiro simulations.

## Architecture

- **Framework**: Vue 3 (Composition API) + Vite 6 + TypeScript
- **Routing**: vue-router 4 (history mode)
- **State**: Pinia + composables for per-sim reactivity
- **Graph**: d3-force + d3-selection + d3-zoom (canvas-free SVG)
- **Markdown**: markdown-it + DOMPurify
- **Realtime**: native `EventSource` against the backend's `/api/simulation/:id/events` SSE endpoint

## Dev setup

```bash
cd web
npm install
npm run dev
```

Vite runs on `localhost:3000` and proxies `/api/*` to `localhost:5001` (set `VITE_API_BASE_URL` env to override).

## Production build

```bash
npm run build
```

The bundle lands in `web/dist/`. Flask serves it at `/` when the `WEB_DIST` env
var points at that directory (set automatically inside the Docker image; for
local `python run.py`, `WEB_DIST` defaults to `../web/dist` relative to the
engine).

## Routes

- `/` — setup form, start a new prediction
- `/history` — past predictions
- `/sim/:simId` — live view with graph + feed
- `/sim/:simId/report` — full markdown report

## API key

Paste once on first load (stored in `localStorage`). The same
`DEEPMIRO_API_KEY` that MCP clients use.

## Design system

Palette + tokens live in `src/styles/theme.css`. All components reference
`var(--*)` — never raw hex. Update the palette in one place to rebrand.
