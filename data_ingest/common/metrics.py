from __future__ import annotations

"""Prometheus Metrics Helpers.

이 모듈은 프로메테우스 `prometheus_client` 라이브러리를 사용해
파이프라인 주요 지표를 노출한다. `init_metrics()`를 가장 먼저 호출하면
HTTP 엔드포인트(`0.0.0.0:{METRICS_PORT}/`)가 열리며 Airflow/CLI 공용으로 사용된다.
"""

import os
import time
from contextlib import contextmanager
from typing import Iterator

import logging
from prometheus_client import Counter, Histogram, Gauge, start_http_server, exposition
from wsgiref.simple_server import make_server

# --------------------------------------------------
# Metric Definitions
# --------------------------------------------------

INGEST_PROCESSED_TOTAL = Counter(
    "ingest_processed_total",
    "Number of raw rows processed",
    labelnames=("source",),
)

INGEST_LATENCY_SECONDS = Histogram(
    "ingest_latency_seconds",
    "Latency for ingest _process function",
    buckets=(0.1, 0.5, 1, 2, 5, 10, 30),
)

EMBEDDING_FAIL_TOTAL = Counter(
    "embedding_fail_total",
    "Number of failed embedding calls",
)

# Timing histogram for DB upsert calls
UPSERT_LATENCY_SECONDS = Histogram(
    "upsert_latency_seconds",
    "Latency for upsert_game_knowledge DB call",
    buckets=(0.005, 0.02, 0.05, 0.1, 0.2, 0.5, 1),
)

# Distribution of quality_score values
QUALITY_SCORE_HISTOGRAM = Histogram(
    "quality_score_bucket",
    "Distribution of quality score for ingested chunks",
    buckets=(0.0, 0.2, 0.4, 0.6, 0.75, 0.85, 0.9, 0.95, 1.0),
)

# RAG query hit / miss counter
RAG_QUERY_TOTAL = Counter(
    "rag_query_total",
    "Number of retrieval queries and whether they resulted in a hit",
    labelnames=("hit",),
)


def record_rag_result(hit: bool):
    """Helper to record retrieval hit/miss result."""
    RAG_QUERY_TOTAL.labels(hit=str(hit).lower()).inc()

_metrics_started = False


def init_metrics() -> None:
    """Start Prometheus exporter HTTP server once per process."""
    global _metrics_started
    if _metrics_started:
        return
    port = int(os.getenv("METRICS_PORT", "8000"))
    # Start prometheus exporter – tolerate address in use
    try:
        start_http_server(port)
        bound_port = port
    except OSError as exc:
        import errno

        if exc.errno == errno.EADDRINUSE:
            logger.warning("Metrics port %s already in use; skipping exporter", port)
            bound_port = None
        else:
            raise

    # Simple healthcheck endpoint on /healthz using wsgi server
    def _health_app(environ, start_response):  # type: ignore[return-type]
        if environ.get("PATH_INFO", "") == "/healthz":
            start_response("200 OK", [("Content-Type", "text/plain")])
            return [b"ok"]
        # fallback to prometheus app
        return exposition.make_wsgi_app()(environ, start_response)

    if bound_port is not None:
        health_port = bound_port + 1
    else:
        # Fallback health port to 0 (OS pick) to avoid clash
        health_port = 0

    def _run_server():
        srv = make_server("0.0.0.0", health_port, _health_app)
        srv.serve_forever()

    import threading  # noqa: WPS433

    th = threading.Thread(target=_run_server, daemon=True)
    th.start()
    _metrics_started = True


@contextmanager
def record_latency(histogram: Histogram):
    """Context manager to time a code block and record to histogram."""
    start = time.perf_counter()
    try:
        yield
    finally:
        duration = time.perf_counter() - start
        histogram.observe(duration) 