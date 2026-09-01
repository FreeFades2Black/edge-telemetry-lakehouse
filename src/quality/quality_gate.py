"""
Multi-Cloud Edge Telemetry & Analytical Lakehouse
Automated Data Quality Scoring & Quarantine Engine.
Enforces schema conformance, range validity, timestamp timeliness, and completeness.
"""

from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Tuple
from src.ingestion.models import EdgeSensorPayload, EnrichedTelemetryRecord, MachineType

class TelemetryQualityGate:
    """Evaluates Bronze raw records against strict quality rules prior to Silver promotion."""

    MAX_DATA_DELAY_MINUTES = 1440  # Max 24h backdated telemetry allowed
    MAX_FUTURE_DRIFT_SECONDS = 300  # Max 5 min future clock drift

    def evaluate_payload(self, raw_dict: Dict[str, Any]) -> Tuple[bool, float, List[str], Dict[str, Any]]:
        """
        Applies data quality rules and computes an overall Quality Score (0-100%).
        Returns: (is_valid, quality_score, failed_rules, cleaned_dict)
        """
        score = 100.0
        failed_rules = []

        # 1. Schema & Required Field Check (40 pts)
        required_fields = ["telemetry_id", "device_id", "machine_type", "vibration_rms_g", "bearing_temp_celsius", "rotational_speed_rpm", "power_draw_kw"]
        missing = [f for f in required_fields if f not in raw_dict or raw_dict[f] is None]
        if missing:
            score -= 40.0
            failed_rules.append(f"MISSING_REQUIRED_FIELDS: {missing}")

        # 2. Sensor Physical Feasibility Check (30 pts)
        vib = raw_dict.get("vibration_rms_g")
        if vib is not None and (vib < 0.0 or vib > 50.0):
            score -= 15.0
            failed_rules.append(f"OUT_OF_BOUNDS_VIBRATION: {vib}G")

        temp = raw_dict.get("bearing_temp_celsius")
        if temp is not None and (temp < -40.0 or temp > 300.0):
            score -= 15.0
            failed_rules.append(f"OUT_OF_BOUNDS_TEMPERATURE: {temp}C")

        rpm = raw_dict.get("rotational_speed_rpm")
        if rpm is not None and (rpm < 0.0 or rpm > 25000.0):
            score -= 10.0
            failed_rules.append(f"OUT_OF_BOUNDS_RPM: {rpm}")

        # 3. Timestamp Temporal Conformance (20 pts)
        ts_val = raw_dict.get("timestamp_utc")
        if ts_val:
            try:
                if isinstance(ts_val, str):
                    ts = datetime.fromisoformat(ts_val.replace("Z", "+00:00"))
                else:
                    ts = ts_val
                now = datetime.now(timezone.utc)
                if ts > now + timedelta(seconds=self.MAX_FUTURE_DRIFT_SECONDS):
                    score -= 20.0
                    failed_rules.append("TEMPORAL_DRIFT_FUTURE_TIMESTAMP")
                elif ts < now - timedelta(minutes=self.MAX_DATA_DELAY_MINUTES):
                    score -= 10.0
                    failed_rules.append("TEMPORAL_DRIFT_STALE_BACKLOG")
            except Exception as e:
                score -= 20.0
                failed_rules.append(f"INVALID_TIMESTAMP_FORMAT: {e}")
        else:
            score -= 20.0
            failed_rules.append("MISSING_TIMESTAMP")

        # 4. Latency & Metadata Sanity (10 pts)
        latency = raw_dict.get("network_latency_ms", 0.0)
        if latency > 1000.0:
            score -= 5.0
            failed_rules.append(f"HIGH_NETWORK_LATENCY: {latency}ms")

        score = max(0.0, round(score, 1))
        is_valid = score >= 70.0 and len(missing) == 0

        return is_valid, score, failed_rules, raw_dict

    def process_bronze_batch(
        self, bronze_records: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        """
        Splits Bronze raw records into Silver Validated and Bronze Quarantine (Dead-Letter).
        Returns: (silver_valid_records, quarantine_dead_letter, batch_quality_metrics)
        """
        silver = []
        quarantine = []
        total_score = 0.0

        for r in bronze_records:
            is_valid, score, failed, cleaned = self.evaluate_payload(r)
            total_score += score
            record_meta = {**cleaned, "quality_score": score, "failed_quality_rules": failed}

            if is_valid:
                silver.append(record_meta)
            else:
                quarantine.append(record_meta)

        count = len(bronze_records)
        avg_score = round(total_score / count, 2) if count > 0 else 100.0
        pass_rate = round((len(silver) / count) * 100, 2) if count > 0 else 100.0

        metrics = {
            "total_evaluated": count,
            "passed_to_silver": len(silver),
            "quarantined_dead_letter": len(quarantine),
            "pass_rate_pct": pass_rate,
            "average_quality_score": avg_score,
            "quality_grade": "PASSED" if pass_rate >= 95.0 else "WARNING"
        }

        return silver, quarantine, metrics
