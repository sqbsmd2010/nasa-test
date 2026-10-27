# OUTPOST: Junior Astronaut Mission Trainer
NASA Space Apps 2026. Run a lunar outpost; balance power, life support, radiation shielding and food.

## Run
```bash
cp .env.example .env            # add your key from https://api.nasa.gov
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --port 8000   # run from repo root
cd frontend && npm install && npm run dev            # http://localhost:5173
```

## Architecture
- `frontend/`: Three.js 3D scene + HUD (Vite, TypeScript)
- `backend/app/sim.py`: server-authoritative sim; incidents are hidden from the client
- `backend/app/nasa.py`: NASA API proxy with caching (API key stays server-side)
