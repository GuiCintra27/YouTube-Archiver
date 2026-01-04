# Observabilidade local (Prometheus + Grafana)

Este setup adiciona um painel visual com Grafana e coleta de metricas via Prometheus.

## Pre-requisitos
- Backend rodando em http://localhost:8000
- Docker + Docker Compose

## Subir o stack
```
docker compose -f docker-compose.observability.yml up -d
```

## Acessos
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001

## Dashboards
- YT-Archiver - Backend Observability (overview + SLO/SLA)
- YT-Archiver - Drive Interactions
- YT-Archiver - Jobs
- YT-Archiver - Downloads

## Alertas (Prometheus)
Alertas basicos de disponibilidade, 5xx e latencia sao definidos em
`ops/observability/alerts.yml`.

Para ver o estado atual:
- http://localhost:9090/alerts

## Observacoes
- O stack usa `network_mode: host` para acessar o backend local via `127.0.0.1`.
- O Prometheus faz scrape de http://127.0.0.1:8000/metrics
- Se o backend estiver em outra porta, ajuste `ops/observability/prometheus.yml`
