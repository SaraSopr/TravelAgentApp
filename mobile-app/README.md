# Travel Agent Mobile

Mobile app React Native (Expo) per il sistema multi-agent TravelAgentApp.

## Features

- autenticazione completa (register/login/logout)
- refresh token automatico su 401
- creazione itinerari complessi (budget, mobilità, interessi)
- dashboard realtime con timeline attività e alert
- simulazione disruption e monitoraggio stato piano
- UX moderna con gradienti, cards e navigazione a tabs
- notifiche locali quando arrivano threat/replan nuovi
- tap sulla notifica apre Home e focalizza il trip coinvolto

## Requisiti

- Node.js 18+
- npm o yarn
- Expo CLI (via npx)
- backend FastAPI attivo

## Setup

```bash
cd mobile-app
nvm use
npm install
npm run start
```

Stable startup (recommended on macOS):

```bash
npm run start:stable
```

From repository root you can also run:

```bash
./scripts/mobile_start.sh
```

Per notifiche su device:

- consenti i permessi quando richiesti dall'app,
- tieni l'app in foreground/background recente per ricevere local alerts da polling.

Apri con Expo Go su iOS/Android oppure emulatore.

## Config API

Base URL in `app.json`:

- `expo.extra.apiBaseUrl` (default: `http://127.0.0.1:8000/api`)

Per device fisico sostituisci con l'IP LAN della macchina backend, es:

- `http://192.168.1.10:8000/api`

## Note

L'app usa gli endpoint backend già implementati:

- `/api/auth/register`
- `/api/auth/login`
- `/api/auth/refresh`
- `/api/auth/logout`
- `/api/trips` (GET/POST)
- `/api/trips/{trip_id}`
- `/api/trips/{trip_id}/alerts`
- `/api/threats/simulate`

## Troubleshooting (Metro EMFILE)

If you see `EMFILE: too many open files, watch`:

1. Use the pinned Node version:

```bash
nvm use
```

2. Install Watchman (macOS):

```bash
HOMEBREW_NO_AUTO_UPDATE=1 brew install watchman
watchman watch-del-all
```

3. Restart Expo:

```bash
npm run start:stable
```
