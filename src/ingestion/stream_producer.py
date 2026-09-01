"""
Multi-Cloud Edge Telemetry & Analytical Lakehouse
Synthetic High-Throughput Edge Telemetry Stream Producer.
Simulates BMW Spartanburg Robotics, Michelin Presses, and GE Vernova Gas Turbines.
"""

import uuid
import random
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Generator
from src.ingestion.models import EdgeSensorPayload, MachineType, PlantLocation

logger = logging.getLogger(__name__)

# Baseline operating parameters per machine class
MACHINE_BASELINES = {
    MachineType.GAS_TURBINE_HA: {
        "vibration_mean": 2.1, "vibration_std": 0.35, "vibration_max_normal": 4.5,
        "temp_mean": 95.0, "temp_std": 6.5, "temp_max_normal": 120.0,
        "rpm_mean": 3600.0, "rpm_std": 15.0,
        "power_mean": 3500.0, "power_std": 120.0,
        "location": PlantLocation.GREENVILLE_SC,
        "devices": ["GEV-TURB-01-GVL", "GEV-TURB-02-GVL", "GEV-TURB-03-GVL"]
    },
    MachineType.AMR_ROBOTIC_ARM: {
        "vibration_mean": 1.4, "vibration_std": 0.25, "vibration_max_normal": 3.2,
        "temp_mean": 52.0, "temp_std": 4.0, "temp_max_normal": 75.0,
        "rpm_mean": 1500.0, "rpm_std": 45.0,
        "power_mean": 45.0, "power_std": 5.5,
        "location": PlantLocation.GREER_SC,
        "devices": ["BMW-ROBOT-KUKA-101", "BMW-ROBOT-KUKA-102", "BMW-AMR-FLEET-204"]
    },
    MachineType.CURING_PRESS: {
        "vibration_mean": 1.8, "vibration_std": 0.30, "vibration_max_normal": 3.8,
        "temp_mean": 170.0, "temp_std": 8.0, "temp_max_normal": 195.0,
        "rpm_mean": 600.0, "rpm_std": 20.0,
        "power_mean": 220.0, "power_std": 18.0,
        "location": PlantLocation.GREENVILLE_SC,
        "devices": ["MICH-PRESS-MARC-01", "MICH-PRESS-MARC-02", "MICH-EXTRUDER-03"]
    },
    MachineType.CNC_MILL_5AXIS: {
        "vibration_mean": 1.1, "vibration_std": 0.20, "vibration_max_normal": 2.8,
        "temp_mean": 48.0, "temp_std": 3.5, "temp_max_normal": 68.0,
        "rpm_mean": 12000.0, "rpm_std": 250.0,
        "power_mean": 35.0, "power_std": 4.0,
        "location": PlantLocation.SPARTANBURG_SC,
        "devices": ["DMG-CNC-5AXIS-301", "DMG-CNC-5AXIS-302"]
    }
}


class EdgeTelemetryProducer:
    """Generates streaming synthetic industrial telemetry batches with configurable anomaly injection."""

    def __init__(self, anomaly_rate: float = 0.08, seed: int = 42):
        self.anomaly_rate = anomaly_rate
        self.rng = random.Random(seed)

    def generate_single_payload(
        self,
        machine_type: MachineType = None,
        force_anomaly: bool = False,
        timestamp_offset_seconds: int = 0
    ) -> EdgeSensorPayload:
        """Generates a single edge sensor telemetry payload."""
        if machine_type is None:
            machine_type = self.rng.choice(list(MACHINE_BASELINES.keys()))

        cfg = MACHINE_BASELINES[machine_type]
        device_id = self.rng.choice(cfg["devices"])
        location = cfg["location"]
        ts = datetime.now(timezone.utc) - timedelta(seconds=timestamp_offset_seconds)

        is_anomaly = force_anomaly or (self.rng.random() < self.anomaly_rate)

        if is_anomaly:
            anomaly_type = self.rng.choice(["BEARING_VIBRATION_SPIKE", "THERMAL_RUNAWAY", "ROTOR_IMBALANCE"])
            if anomaly_type == "BEARING_VIBRATION_SPIKE":
                vib = cfg["vibration_mean"] + self.rng.uniform(3.5, 9.0)
                temp = cfg["temp_mean"] + self.rng.uniform(5.0, 15.0)
                rpm = cfg["rpm_mean"] + self.rng.gauss(0, cfg["rpm_std"])
            elif anomaly_type == "THERMAL_RUNAWAY":
                vib = cfg["vibration_mean"] + self.rng.gauss(0, cfg["vibration_std"])
                temp = cfg["temp_max_normal"] + self.rng.uniform(15.0, 45.0)
                rpm = cfg["rpm_mean"] * 0.9
            else: # ROTOR_IMBALANCE
                vib = cfg["vibration_mean"] * 2.8
                temp = cfg["temp_mean"] + self.rng.uniform(8.0, 20.0)
                rpm = cfg["rpm_mean"] * self.rng.uniform(1.15, 1.35)
        else:
            vib = max(0.1, self.rng.gauss(cfg["vibration_mean"], cfg["vibration_std"]))
            temp = max(10.0, self.rng.gauss(cfg["temp_mean"], cfg["temp_std"]))
            rpm = max(100.0, self.rng.gauss(cfg["rpm_mean"], cfg["rpm_std"]))

        power = max(1.0, self.rng.gauss(cfg["power_mean"], cfg["power_std"]))
        psi = self.rng.uniform(1800.0, 3200.0) if machine_type in [MachineType.CURING_PRESS, MachineType.CNC_MILL_5AXIS] else None
        acoustic = self.rng.uniform(65.0, 115.0) if is_anomaly else self.rng.uniform(55.0, 80.0)

        return EdgeSensorPayload(
            telemetry_id=str(uuid.uuid4()),
            device_id=device_id,
            machine_type=machine_type,
            facility_location=location,
            timestamp_utc=ts,
            vibration_rms_g=round(vib, 3),
            bearing_temp_celsius=round(temp, 2),
            rotational_speed_rpm=round(rpm, 1),
            power_draw_kw=round(power, 2),
            hydraulic_pressure_psi=round(psi, 1) if psi else None,
            acoustic_emission_db=round(acoustic, 1),
            firmware_version="v2.4.1",
            network_latency_ms=round(self.rng.uniform(8.0, 35.0), 1),
            is_simulated_anomaly=is_anomaly
        )

    def generate_batch(self, count: int = 500) -> List[EdgeSensorPayload]:
        """Generates a batch of N telemetry records."""
        return [self.generate_single_payload(timestamp_offset_seconds=i * 2) for i in range(count)]

    def generate_json_batch(self, count: int = 500) -> str:
        """Returns JSON string for Kinesis or LocalStack injection."""
        batch = self.generate_batch(count)
        return json.dumps([p.model_dump(mode="json") for p in batch], indent=2)
