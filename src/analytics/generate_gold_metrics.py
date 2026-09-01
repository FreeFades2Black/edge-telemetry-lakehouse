"""
Multi-Cloud Edge Telemetry & Analytical Lakehouse
Gold Layer Metrics & Fleet Telemetry Aggregator (generate_gold_metrics.py)
"""

import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.processing.delta_lakehouse import EdgeTelemetryLakehousePipeline


def generate_gold_layer_metrics() -> dict:
    """Executes Lakehouse pipeline and generates Gold fleet health summary."""
    pipeline = EdgeTelemetryLakehousePipeline()

    # 1. Ingest historical NASA C-MAPSS + CWRU benchmarks
    print("[1/3] Replaying NASA C-MAPSS and CWRU benchmark logs into Bronze...")
    pipeline.run_historical_benchmark_replay(dataset_key="nasa_cmapss", limit=50)

    # 2. Process Silver with ISO 10816 Anomaly Engine & Quality Gating
    print("[2/3] Processing Silver Layer & executing ISO 10816 Quality Gates...")
    silver_res = pipeline.run_silver_processing()

    # 3. Aggregate Gold Layer Fleet Health
    print("[3/3] Aggregating Gold Layer Fleet Health & Machine Health Indices...")
    gold_res = pipeline.run_gold_aggregation()

    print(f"Successfully generated Gold Layer Metrics: {gold_res['machines_evaluated']} machines evaluated.")
    return gold_res


if __name__ == "__main__":
    generate_gold_layer_metrics()
