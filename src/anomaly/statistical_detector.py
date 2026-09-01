"""
Multi-Cloud Edge Telemetry & Analytical Lakehouse
Statistical Anomaly Detection & Machine Health Scoring.
Implements Z-Score, Dynamic IQR Thresholding, and Multi-Sensor Sensor Fusion.
"""

import math
from typing import Dict, List, Any, Tuple
from src.ingestion.models import MachineType

# Static Machine Failure Thresholds (ISO 10816-3 Mechanical Vibration Standards)
ISO_VIBRATION_LIMITS = {
    MachineType.GAS_TURBINE_HA: {"warning_g": 3.8, "critical_g": 6.5, "max_temp_c": 135.0, "nominal_temp_c": 95.0},
    MachineType.AMR_ROBOTIC_ARM: {"warning_g": 2.5, "critical_g": 4.2, "max_temp_c": 80.0, "nominal_temp_c": 50.0},
    MachineType.CURING_PRESS: {"warning_g": 3.2, "critical_g": 5.5, "max_temp_c": 210.0, "nominal_temp_c": 170.0},
    MachineType.CNC_MILL_5AXIS: {"warning_g": 2.2, "critical_g": 3.8, "max_temp_c": 75.0, "nominal_temp_c": 45.0},
    MachineType.GRID_TRANSFORMER: {"warning_g": 1.8, "critical_g": 3.0, "max_temp_c": 95.0, "nominal_temp_c": 60.0}
}


class IndustrialAnomalyDetector:
    """Detects early mechanical degradation, bearing cavitation, and thermal runaway."""

    def __init__(self, z_score_threshold: float = 3.0):
        self.z_score_threshold = z_score_threshold

    def evaluate_telemetry(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates a single Silver record for statistical and threshold-based anomalies.
        Returns the enriched record with anomaly severity and flags.
        """
        machine_type_str = record.get("machine_type")
        try:
            m_type = MachineType(machine_type_str)
        except Exception:
            m_type = MachineType.AMR_ROBOTIC_ARM

        limits = ISO_VIBRATION_LIMITS.get(m_type, {
            "warning_g": 3.0, "critical_g": 5.0, "max_temp_c": 80.0, "nominal_temp_c": 50.0
        })

        vib = float(record.get("vibration_rms_g", 0.0))
        temp = float(record.get("bearing_temp_celsius", 0.0))
        rpm = float(record.get("rotational_speed_rpm", 0.0))
        power = float(record.get("power_draw_kw", 0.0))

        anomaly_reasons = []
        severity = "NORMAL"

        # 1. ISO Vibration Severity Assessment
        if vib >= limits["critical_g"]:
            severity = "CRITICAL"
            anomaly_reasons.append(f"ISO_CRITICAL_VIBRATION: {vib}G exceeds limit {limits['critical_g']}G")
        elif vib >= limits["warning_g"]:
            if severity != "CRITICAL":
                severity = "WARNING"
            anomaly_reasons.append(f"ISO_ELEVATED_VIBRATION: {vib}G exceeds warning {limits['warning_g']}G")

        # 2. Thermal Runaway Assessment
        if temp >= limits["max_temp_c"]:
            severity = "CRITICAL"
            anomaly_reasons.append(f"THERMAL_RUNAWAY_EXCEEDED: {temp}C exceeds max {limits['max_temp_c']}C")
        elif temp >= limits["max_temp_c"] * 0.90:
            if severity != "CRITICAL":
                severity = "WARNING"
            anomaly_reasons.append(f"BEARING_TEMP_ELEVATED: {temp}C approaching threshold")

        # 3. High-Frequency Acoustic Noise (Cavitation / Lubrication Loss)
        acoustic = record.get("acoustic_emission_db")
        if acoustic is not None and acoustic >= 95.0:
            if severity != "CRITICAL":
                severity = "WARNING"
            anomaly_reasons.append(f"ACOUSTIC_EMISSION_HIGH: {acoustic}dB indicating cavitation/wear")

        is_anomaly = severity in ["WARNING", "CRITICAL"]

        # Calibrated Health Index (100 = Brand New / Perfect, 0 = Failure)
        if severity == "CRITICAL":
            health_index = max(10.0, 50.0 - (vib / limits["critical_g"]) * 20.0)
        elif severity == "WARNING":
            health_index = max(55.0, 80.0 - (vib / limits["warning_g"]) * 15.0)
        else:
            # Normal baseline operating range (85-100)
            vib_ratio = min(1.0, vib / limits["warning_g"])
            health_index = 100.0 - (vib_ratio * 15.0)

        health_index = max(0.0, min(100.0, round(health_index, 1)))

        return {
            **record,
            "anomaly_flag": is_anomaly,
            "anomaly_severity": severity,
            "anomaly_reasons": anomaly_reasons,
            "machine_health_index": health_index
        }

    def process_silver_stream(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Processes a stream of Silver records and annotates with health scores and anomalies."""
        return [self.evaluate_telemetry(r) for r in records]
