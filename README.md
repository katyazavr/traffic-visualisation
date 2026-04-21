# Traffic visualisation

## Implementation
- `sender`: reads CSV and sends packets by timestamp intervals
- `backend`: Flask API to receive packets and stream them to frontend
- `frontend`: Three.js globe-based visualisation with interactions

## Run with Docker Compose

```bash
docker compose up --build
```

Then open:
- Frontend: `http://localhost:8080`
- Backend health endpoint: `http://localhost:5000/`

## API

- `POST /packet` receive a packet
- `GET /packet?limit=100` fetch latest packets
- `GET /stats` receive total, suspicious and top locations
- `GET /stream` server-sent events stream for live packets

## Frontend interactions

- Pause/resume live stream
- Filter to show suspicious packets only
- Live-updating top locations panel
