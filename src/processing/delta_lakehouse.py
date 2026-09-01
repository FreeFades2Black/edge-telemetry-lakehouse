"""
Multi-Cloud Edge Telemetry & Analytical Lakehouse
Medallion Delta Lakehouse Analytics Engine (Bronze -> Silver -> Gold).
Simulates Delta Lake parquet partition operations and computes Gold Machine Health Aggregations.
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any
from src.ingestion.stream_producer import EdgeTelemetryProducer
from src.quality.quality_gate import TelemetryQualityGate
from src.anomaly.statistical_detector import IndustrialAnomalyDetector

BASE_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
BRONZE_DIR = BASE_DATA_DIR / "bronze"
SILVER_DIR = BASE_DATA_DIR / "silver"
GOLD_DIR = BASE_DATA_DIR / "gold"
QUARANTINE_DIR = BASE_DATA_DIR / "quarantine"

for d in [BRONZE_DIR, SILVER_DIR, GOLD_DIR, QUARANTINE_DIR]:
    d.mkdir(parents=True, exist_ok=True)


class EdgeTelemetryLakehousePipeline:
    """Executes the full Medallion Lakehouse pipeline for Industrial Edge Telemetry."""

    def __init__(self):
        self.producer = EdgeTelemetryProducer()
        self.quality_gate = TelemetryQualityGate()
        self.anomaly_detector = IndustrialAnomalyDetector()

    def run_bronze_ingestion(self, record_count: int = 500) -> Dict[str, Any]:
        """Ingests raw streaming edge batches into Bronze Lakehouse partition."""
        raw_payloads = self.producer.generate_batch(record_count)
        raw_dicts = [p.model_dump(mode="json") for p in raw_payloads]

        timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        bronze_file = BRONZE_DIR / f"bronze_telemetry_{timestamp_str}.json"
        bronze_latest = BRONZE_DIR / "bronze_telemetry_latest.json"

        with open(bronze_file, "w", encoding="utf-8") as f:
            json.dump(raw_dicts, f, indent=2)
        with open(bronze_latest, "w", encoding="utf-8") as f:
            json.dump(raw_dicts, f, indent=2)

        return {
            "tier": "BRONZE",
            "status": "SUCCESS",
            "records_ingested": len(raw_dicts),
            "output_file": str(bronze_file)
        }

    def run_silver_processing(self) -> Dict[str, Any]:
        """Validates Bronze telemetry via Quality Gate and applies Anomaly Detection."""
        bronze_latest = BRONZE_DIR / "bronze_telemetry_latest.json"
        if not bronze_latest.exists():
            self.run_bronze_ingestion(300)

        with open(bronze_latest, "r", encoding="utf-8") as f:
            raw_records = json.load(f)

        valid_records, quarantined_records, q_metrics = self.quality_gate.process_bronze_batch(raw_records)

        # Apply Industrial Anomaly Detection to Valid Silver records
        enriched_silver = self.anomaly_detector.process_silver_stream(valid_records)

        silver_file = SILVER_DIR / "silver_enriched_telemetry.json"
        quarantine_file = QUARANTINE_DIR / "quarantined_telemetry.json"

        with open(silver_file, "w", encoding="utf-8") as f:
            json.dump(enriched_silver, f, indent=2)
        with open(quarantine_file, "w", encoding="utf-8") as f:
            json.dump(quarantined_records, f, indent=2)

        return {
            "tier": "SILVER",
            "status": "SUCCESS",
            "valid_silver_records": len(enriched_silver),
            "quarantined_records": len(quarantined_records),
            "quality_metrics": q_metrics,
            "output_file": str(silver_file)
        }

    def run_gold_aggregation(self) -> Dict[str, Any]:
        """Computes Gold Fleet Health Summaries, Machine Risk Leaderboard, and OEE Metrics."""
        silver_file = SILVER_DIR / "silver_enriched_telemetry.json"
        if not silver_file.exists():
            self.run_silver_processing()

        with open(silver_file, "r", encoding="utf-8") as f:
            silver_records = json.load(f)

        device_stats: Dict[str, Dict[str, Any]] = {}
        plant_stats: Dict[str, Dict[str, Any]] = {}

        for r in silver_records:
            dev = r["device_id"]
            plant = r["facility_location"]
            m_type = r["machine_type"]
            vib = r["vibration_rms_g"]
            temp = r["bearing_temp_celsius"]
            health = r.get("machine_health_index", 100.0)
            is_anomaly = r.get("anomaly_flag", False)
            severity = r.get("anomaly_severity", "NORMAL")

            # Aggregate per device
            if dev not in device_stats:
                device_stats[dev] = {
                    "device_id": dev,
                    "machine_type": m_type,
                    "facility_location": plant,
                    "total_telemetry_samples": 0,
                    "sum_vibration": 0.0,
                    "max_vibration": 0.0,
                    "sum_temp": 0.0,
                    "max_temp": 0.0,
                    "sum_health": 0.0,
                    "anomaly_count": 0,
                    "critical_anomaly_count": 0,
                    "latest_severity": severity
                }

            s = device_stats[dev]
            s["total_telemetry_samples"] += 1
            s["sum_vibration"] += vib
            s["max_vibration"] = max(s["max_vibration"], vib)
            s["sum_temp"] += temp
            s["max_temp"] = max(s["max_temp"], temp)
            s["sum_health"] += health
            if is_anomaly:
                s["anomaly_count"] += 1
            if severity == "CRITICAL":
                s["critical_anomaly_count"] += 1
            s["latest_severity"] = severity

            # Aggregate per plant
            if plant not in plant_stats:
                plant_stats[plant] = {
                    "facility_location": plant,
                    "total_samples": 0,
                    "total_anomalies": 0,
                    "machines_monitored": set()
                }
            plant_stats[plant]["total_samples"] += 1
            if is_anomaly:
                plant_stats[plant]["total_anomalies"] += 1
            plant_stats[plant]["machines_monitored"].add(dev)

        gold_device_summary = []
        for dev, s in device_stats.items():
            n = s["total_telemetry_samples"]
            avg_vib = round(s["sum_vibration"] / n, 2) if n > 0 else 0.0
            avg_temp = round(s["sum_temp"] / n, 1) if n > 0 else 0.0
            avg_health = round(s["sum_health"] / n, 1) if n > 0 else 100.0
            anomaly_rate = round((s["anomaly_count"] / n) * 100, 2) if n > 0 else 0.0

            status = "HEALTHY"
            if s["critical_anomaly_count"] > 0 or avg_health < 65.0:
                status = "CRITICAL_ACTION_REQUIRED"
            elif s["anomaly_count"] > 0 or avg_health < 85.0:
                status = "MAINTENANCE_WARNING"

            gold_device_summary.append({
                "device_id": dev,
                "machine_type": s["machine_type"],
                "facility_location": s["facility_location"],
                "samples_evaluated": n,
                "avg_vibration_rms_g": avg_vib,
                "peak_vibration_rms_g": round(s["max_vibration"], 2),
                "avg_bearing_temp_c": avg_temp,
                "peak_bearing_temp_c": round(s["max_temp"], 1),
                "machine_health_score": avg_health,
                "anomaly_rate_pct": anomaly_rate,
                "maintenance_status": status
            })

        gold_device_summary.sort(key=lambda x: x["machine_health_score"])

        gold_plant_summary = []
        for plant, p in plant_stats.items():
            tot = p["total_samples"]
            anom_pct = round((p["total_anomalies"] / tot) * 100, 2) if tot > 0 else 0.0
            gold_plant_summary.append({
                "facility_location": plant,
                "machines_monitored_count": len(p["machines_monitored"]),
                "total_telemetry_events": tot,
                "anomaly_rate_pct": anom_pct,
                "plant_operational_reliability_pct": round(100.0 - anom_pct, 2)
            })

        gold_output = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "fleet_machines_summary": gold_device_summary,
            "plant_location_summary": gold_plant_summary
        }

        gold_file = GOLD_DIR / "gold_fleet_machine_health.json"
        with open(gold_file, "w", encoding="utf-8") as f:
            json.dump(gold_output, f, indent=2)

        return {
            "tier": "GOLD",
            "status": "SUCCESS",
            "machines_evaluated": len(gold_device_summary),
            "plants_evaluated": len(gold_plant_summary),
            "output_file": str(gold_file)
        }
