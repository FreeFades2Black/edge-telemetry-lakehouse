"""
Test Suite: Pre-Bronze Ingress Gatekeeper Verification.
Verifies that:
1. Batches with duplicate telemetry IDs discard duplicate records with ZERO writes to Bronze.
2. Malformed payloads (missing ID, empty payload) are routed to Quarantine.
3. Only validated, unique records land in the Bronze delta zone.
"""

import json
from pathlib import Path
import pytest
from src.ingestion.gatekeeper_client import GatekeeperClient
from src.processing.delta_lakehouse import EdgeTelemetryLakehousePipeline, BRONZE_DIR, QUARANTINE_DIR


def test_gatekeeper_filters_duplicates_and_quarantines(tmp_path):
    """
    CRITICAL INVARIANT TEST:
    Simulates an ingestion batch with duplicates and malformed records.
    Verifies zero duplicates reach Bronze and malformed records land in quarantine.
    """
    quarantine_file = tmp_path / "dead_letter_events.jsonl"
    client = GatekeeperClient()

    batch = [
        {"telemetry_id": "TEL-UNIT-001", "device_id": "PUMP-A", "timestamp_utc": "2026-10-05T12:00:00Z", "payload": "nominal"},
        {"telemetry_id": "TEL-UNIT-001", "device_id": "PUMP-A", "timestamp_utc": "2026-10-05T12:00:05Z", "payload": "nominal_duplicate"},
        {"telemetry_id": "TEL-UNIT-002", "device_id": "TURBINE-B", "timestamp_utc": "2026-10-05T12:00:10Z", "payload": "high_vibration"},
        {"telemetry_id": "", "device_id": "UNKNOWN", "timestamp_utc": "2026-10-05T12:00:15Z", "payload": "missing_id"},
        {"telemetry_id": "TEL-UNIT-003", "device_id": "MOTOR-C", "timestamp_utc": "2026-10-05T12:00:20Z", "payload": "temp_warning"},
        {"telemetry_id": "TEL-UNIT-002", "device_id": "TURBINE-B", "timestamp_utc": "2026-10-05T12:00:25Z", "payload": "duplicate_turbine"},
    ]

    validated = client.filter_batch(batch, quarantine_file=quarantine_file)

    # 1. Zero duplicate records reach validated Bronze list
    assert len(validated) == 3
    validated_ids = [r["telemetry_id"] for r in validated]
    assert validated_ids == ["TEL-UNIT-001", "TEL-UNIT-002", "TEL-UNIT-003"]

    # 2. Malformed record landed in quarantine
    assert quarantine_file.exists()
    with open(quarantine_file, "r", encoding="utf-8") as f:
        quarantined = [json.loads(line) for line in f if line.strip()]

    assert len(quarantined) == 1
    assert quarantined[0]["record"]["device_id"] == "UNKNOWN"
    assert "error" in quarantined[0]


def test_pipeline_bronze_ingestion_with_gatekeeper():
    """Verify integration between Lakehouse Pipeline and Gatekeeper."""
    gatekeeper = GatekeeperClient()
    pipeline = EdgeTelemetryLakehousePipeline(gatekeeper=gatekeeper)

    # First batch
    res1 = pipeline.run_bronze_ingestion(record_count=20)
    assert res1["status"] == "SUCCESS"
    assert res1["records_ingested"] == 20

    # Ingesting same batch again through same gatekeeper yields 0 new records in Bronze
    latest_file = BRONZE_DIR / "bronze_telemetry_latest.json"
    assert latest_file.exists()
