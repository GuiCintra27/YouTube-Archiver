# Local observability (Prometheus + Grafana)

[PT-BR](../OBSERVABILITY.md) | **EN**

This setup adds a visual dashboard with Grafana and metrics collection via Prometheus.

## Prerequisites
- Backend running at http://localhost:8000
- Docker + Docker Compose

## Up the stack
```
docker compose -f docker-compose.observability.yml up -d
```

## Hits
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001

## Dashboards
- YT-Archiver - Backend Observability (overview + SLO/SLA)
- YT-Archiver - Drive Interactions
- YT-Archiver - Jobs
- YT-Archiver - Downloads

## Alerts (Prometheus)
Basic availability, 5xx and latency alerts are defined in
`ops/observability/alerts.yml`.

To see the current status:
- http://localhost:9090/alerts

## Observations
- The stack uses `network_mode: host` to access the local backend via `127.0.0.1`.
- Prometheus scrapes http://127.0.0.1:8000/metrics
- If the backend is on another port, set `ops/observability/prometheus.yml`
