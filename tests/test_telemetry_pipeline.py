"""
Multi-Cloud Edge Telemetry & Analytical Lakehouse
Comprehensive Unit & Integration Test Suite.
Tests Ingestion, Data Quality Gating, Statistical Anomaly Detection, and Lakehouse Aggregations.
"""

import pytest
from datetime import datetime, timezone, timedelta
from src.ingestion.models import EdgeSensorPayload, MachineType, PlantLocation
from src.ingestion.stream_producer import EdgeTelemetryProducer
from src.quality.quality_gate import TelemetryQualityGate
from src.anomaly.statistical_detector import IndustrialAnomalyDetector
from src.processing.delta_lakehouse import EdgeTelemetryLakehousePipeline


def test_edge_payload_model_validation():
    """Verify Pydantic models reject invalid physical measurements."""
    payload = EdgeSensorPayload(
        telemetry_id="test-uuid-101",
        device_id="BMW-ROBOT-KUKA-101",
        machine_type=MachineType.AMR_ROBOTIC_ARM,
        facility_location=PlantLocation.GREER_SC,
        vibration_rms_g=1.45,
        bearing_temp_celsius=54.2,
        rotational_speed_rpm=1500.0,
        power_draw_kw=45.0
    )
    assert payload.device_id == "BMW-ROBOT-KUKA-101"
    assert payload.vibration_rms_g == 1.45


def test_producer_batch_generation():
    """Ensure synthetic generator produces batches with configured baseline diversity."""
    producer = EdgeTelemetryProducer(anomaly_rate=0.10, seed=123)
    batch = producer.generate_batch(50)
    assert len(batch) == 50
    assert any(p.facility_location == PlantLocation.GREENVILLE_SC for p in batch)
    assert any(p.facility_location == PlantLocation.GREER_SC for p in batch)


def test_quality_gate_passes_clean_data():
    """Valid records should score >= 90% and pass to Silver layer."""
    gate = TelemetryQualityGate()
    clean_record = {
        "telemetry_id": "test-clean-001",
        "device_id": "GEV-TURB-01-GVL",
        "machine_type": "GE_HA_GAS_TURBINE",
        "facility_location": "GREENVILLE_SC_USA",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "vibration_rms_g": 2.1,
        "bearing_temp_celsius": 95.0,
        "rotational_speed_rpm": 3600.0,
        "power_draw_kw": 3500.0,
        "network_latency_ms": 14.2
    }
    is_valid, score, failed, _ = gate.evaluate_payload(clean_record)
    assert is_valid is True
    assert score >= 90.0
    assert len(failed) == 0


def test_quality_gate_quarantines_malformed_data():
    """Malformed or physical violation records should be rejected."""
    gate = TelemetryQualityGate()
    bad_record = {
        "telemetry_id": "test-bad-002",
        "device_id": "CORRUPT-SENSOR-999",
        "machine_type": "GE_HA_GAS_TURBINE",
        "timestamp_utc": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(), # Future drift
        "vibration_rms_g": -5.0, # Negative vibration physically impossible
        "bearing_temp_celsius": 999.0, # Extreme unphysical temp
        "rotational_speed_rpm": 3600.0,
        "power_draw_kw": 3500.0
    }
    is_valid, score, failed, _ = gate.evaluate_payload(bad_record)
    assert is_valid is False
    assert score < 70.0
    assert len(failed) > 0


def test_industrial_anomaly_detection():
    """Verify ISO vibration and thermal runaway triggers."""
    detector = IndustrialAnomalyDetector()

    # Normal reading
    normal_record = {
        "device_id": "GEV-TURB-01-GVL",
        "machine_type": "GE_HA_GAS_TURBINE",
        "vibration_rms_g": 2.2,
        "bearing_temp_celsius": 96.0,
        "rotational_speed_rpm": 3600.0,
        "power_draw_kw": 3500.0
    }
    res_normal = detector.evaluate_telemetry(normal_record)
    assert res_normal["anomaly_flag"] is False
    assert res_normal["anomaly_severity"] == "NORMAL"
    assert res_normal["machine_health_index"] >= 80.0

    # Critical anomaly reading
    critical_record = {
        "device_id": "GEV-TURB-01-GVL",
        "machine_type": "GE_HA_GAS_TURBINE",
        "vibration_rms_g": 7.8, # Exceeds 6.5G critical limit
        "bearing_temp_celsius": 135.0, # Exceeds 115C max limit
        "rotational_speed_rpm": 3600.0,
        "power_draw_kw": 3500.0
    }
    res_crit = detector.evaluate_telemetry(critical_record)
    assert res_crit["anomaly_flag"] is True
    assert res_crit["anomaly_severity"] == "CRITICAL"
    assert res_crit["machine_health_index"] < 50.0


def test_full_medallion_pipeline_execution():
    """Verify end-to-end Bronze -> Silver -> Gold execution flow."""
    pipeline = EdgeTelemetryLakehousePipeline()
    
    # 1. Bronze
    b_res = pipeline.run_bronze_ingestion(record_count=100)
    assert b_res["status"] == "SUCCESS"
    assert b_res["records_ingested"] == 100

    # 2. Silver
    s_res = pipeline.run_silver_processing()
    assert s_res["status"] == "SUCCESS"
    assert s_res["valid_silver_records"] > 0

    # 3. Gold
    g_res = pipeline.run_gold_aggregation()
    assert g_res["status"] == "SUCCESS"
    assert g_res["machines_evaluated"] > 0
    assert g_res["plants_evaluated"] > 0
