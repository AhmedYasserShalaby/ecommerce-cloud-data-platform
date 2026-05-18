# Streaming

The project includes a local-first streaming path plus Redpanda service wiring in Docker Compose.

Local smoke path:

```bash
commerce-platform stream-produce --profile ci --events 250
commerce-platform stream-consume --profile ci
commerce-platform run-spark --profile ci
```

Behavior:

- Producer writes deterministic e-commerce web events.
- Consumer tracks checkpoint offsets.
- Re-runs do not duplicate already-consumed events.
- Micro-batches land as Parquet under `data/lake/bronze_stream`.
- Silver web events include batch and consumed streaming events.
- Quality reports export streaming freshness.

Docker Redpanda is included to show production mapping without making CI depend on a broker.
