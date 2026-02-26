# TravelAgentApp

Event-driven multi-agent system to mitigate LLM knowledge cutoff in dynamic urban environments, with integrated frontend dashboard.

## Vision

Traditional LLM planning is static after training. In high-entropy cities (strikes, protests, incidents), this creates a temporal gap between generated plans and reality. TravelAgentApp closes this gap with three cooperating agents:

- Planner: intent decoding, initial itinerary generation, temporal-path plan modeling.
- Observer: asynchronous monitoring of heterogeneous streams (news, transit, social).
- Mind: conflict-aware impact assessment and proactive re-planning decisions.

## System Architecture

- Architecture style: Event-Driven + actor-like isolated agents.
- Messaging pattern: Pub/Sub topics for events; command topics for explicit actions.
- Consistency model: Eventual consistency with idempotent consumers.
- Runtime: Async Python + FastAPI + event bus (inmemory or NATS).

### Core Event Flow

1. API publishes `trip.command.create`.
2. Planner creates baseline plan and emits `trip.event.created`.
3. Observer emits `obs.event.detected` from external signals.
4. Mind computes Threat x Path impact and emits `mind.event.assessed`.
5. If threshold exceeded, Mind emits `trip.command.replan`.
6. Planner patches itinerary and emits `trip.event.updated`.

## Project Structure

```text
app/
  agents/
    planner.py
    observer.py
    mind.py
  api/
    routes.py
  bus/
    base.py
    in_memory.py
    nats_bus.py
  connectors/
    observer_sources.py
  core/
    config.py
    logging.py
    tracing.py
  domain/
    events.py
    models.py
    scoring.py
  services/
    orchestrator.py
  state/
    memory.py
    repository.py
  web/
    routes.py
    ui/index.html
  main.py
tests/
  test_api.py
  test_ops_endpoints.py
  test_scoring.py
  test_bus_resilience.py
```

## Data Contracts (Pydantic)

- EventEnvelope: event metadata, correlation/causation IDs, sequence, confidence.
- CreateTripRequest: user intent input contract.
- Plan, Activity: dynamic itinerary representation.
- ThreatEvent: normalized signal from observer sources.
- ImpactAssessment: mind decision output.

## Communication Model

### Topics

- `trip.command.create`
- `trip.event.created`
- `obs.event.detected`
- `mind.event.assessed`
- `trip.command.replan`
- `trip.event.updated`
- `system.event.failed`

### Reliability

- At-least-once delivery.
- Deduplication by `event_id`.
- Correlation tracing by `correlation_id`.
- Per-trip sequencing using `aggregate_id=trip_id`.
- Retry with exponential backoff + DLQ for poison events.

## State and Memory Strategy

- PlanRepository: operational trip state (in-memory now; Postgres-ready).
- EventHistoryRepository: append-only event history with dedup.
- DecisionMemory: anti-flapping replan cooldown logic.

This separates short-term operational state from decision memory and event lineage.

## Frontend (Integrated)

The dashboard is served directly by FastAPI at `/`.

From the UI you can:

- create new trips,
- select active trips,
- simulate threats,
- monitor event flow,
- inspect DLQ state.

End-user realistic UX includes:

- travel profile setup (budget, mobility mode, interests, departure time),
- itinerary timeline cards with cost and transport hints,
- trip-level alert feed (threat/assessment/replan) in near real-time,
- visible plan status and risk evolution after disruptions.

Base authentication is enabled via:

- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/refresh`
- `POST /api/auth/logout`

User-facing trip endpoints require `Authorization: Bearer <token>`.
Login endpoint includes basic rate limiting per username/client source.
Repeated failed logins trigger temporary lockout based on:

- `AUTH_LOGIN_MAX_ATTEMPTS`
- `AUTH_LOGIN_WINDOW_SECONDS`
- `AUTH_LOGIN_LOCK_SECONDS`

## Local Run

### 1) Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

Optional extras:

```bash
pip install -e .[dev,nats,otel]
```

For Postgres persistence in local non-docker runs, set:

```bash
export STATE_BACKEND=postgres
```

### 2) Start API + Frontend

```bash
python -m uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/
```

### 3) Optional infrastructure (NATS/Postgres/Redis)

```bash
docker compose up -d
```

Set `BUS_BACKEND=nats` in `.env` to use NATS.

## One-command Docker Run (Backend + Frontend + Infra)

Build and run everything:

```bash
docker compose up --build
```

Recommended detached startup:

```bash
docker compose up --build -d
docker compose ps
```

Open:

```text
http://127.0.0.1:8000/
```

If you see transient `context canceled` while pulling images, rerun the command once. The stack now includes startup health checks and NATS connect retries to reduce race failures.

### 4) Run tests

```bash
pytest -q
```

## Ops Endpoints

- `/api/ops/plans`
- `/api/ops/events`
- `/api/ops/dlq`
- `/api/ops/auth-audit`

## User Endpoints

- `/api/auth/register`
- `/api/auth/login`
- `/api/trips` (GET/POST, auth required)
- `/api/trips/{trip_id}` (auth required)
- `/api/trips/{trip_id}/alerts` (auth required)

## Mobile App (React Native Expo)

The repository now includes a full mobile client at `mobile-app/` with:

- modern multi-screen UX,
- auth + token refresh,
- trip creation and realtime monitoring,
- disruption simulation and adaptive itinerary visualization.

Quick start:

```bash
cd mobile-app
npm install
npm run start
```

Configure backend base URL in `mobile-app/app.json` (`expo.extra.apiBaseUrl`).

### One-command Local Dev (Backend + Mobile)

From repository root:

```bash
./scripts/dev_all.sh
```

Only mobile (stable startup):

```bash
./scripts/mobile_start.sh
```

## Testing Strategy

### Unit Tests

- Scoring and deterministic conflict-impact logic.
- Bus retry/DLQ behavior.

### Integration Tests

- API create trip flow.
- Frontend root route serving.
- Ops endpoints availability.

### Resilience Tests (next phase)

- Duplicate/out-of-order events under load.
- Burst threat load (event storm).
- Source conflict stress scenarios.

## Cloud Deployment Readiness

- Stateless service layer with externalized bus/store.
- Twelve-factor configuration via env vars.
- Async non-blocking processing.
- Clear boundaries for horizontal scaling per agent type.

## Architectural Risks and Bottlenecks

1. Event storm amplification during city-scale incidents.
   - Mitigation: backpressure, priority routing, rate limiting.
2. Conflicting source truth (high-noise social feeds).
   - Mitigation: trust weighting + corroboration + uncertainty mode.
3. Replan oscillation from frequent low-confidence alerts.
   - Mitigation: cooldown/hysteresis in DecisionMemory.
4. Latency spikes from LLM calls.
   - Mitigation: bounded timeouts, cached heuristics, fallback rules.
5. Poison messages causing repeated failures.
   - Mitigation: retry policy + DLQ and failure topic routing.
