"""
Multi-Cloud Edge Telemetry & Analytical Lakehouse
Gunslinger Historical Telemetry Replay Engine (revolver_replay.py)
LORE: The Gunslinger draws from old trail markers to sight the target ahead.

Replays verified historical industrial benchmark datasets:
  1. NASA Prognostics Center of Excellence (PCoE) Turbofan Degradation (C-MAPSS)
  2. Case Western Reserve University (CWRU) Bearing Data Center
  3. AI4I 2020 Predictive Maintenance Dataset (UCI ML Repository)
"""

import csv
import json
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Generator, List, Dict, Any, Optional

BENCHMARK_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "benchmarks"


@dataclass(frozen=True)
class TelemetryFrame:
    """Standardized industrial telemetry frame for ingestion into Bronze Lakehouse."""
    telemetry_id: str
    device_id: str
    machine_type: str
    facility_location: str
    timestamp_utc: str
    vibration_rms_g: float
    bearing_temp_celsius: float
    rotational_speed_rpm: float
    power_draw_kw: float
    hydraulic_pressure_psi: Optional[float]
    acoustic_emission_db: Optional[float]
    dataset_source: str
    is_fault_state: bool


class HistoricalTelemetryReplay:
    """Replays historical benchmark telemetry logs into the Lakehouse ingestion bus."""

    DATASET_FILES = {
        "nasa_cmapss": BENCHMARK_DATA_DIR / "nasa_cmapss_turbofan_sample.csv",
        "cwru_bearing": BENCHMARK_DATA_DIR / "cwru_bearing_vibration_sample.csv",
        "ai4i2020": BENCHMARK_DATA_DIR / "ai4i2020_predictive_maintenance_sample.csv"
    }

    def __init__(self, dataset_key: str = "nasa_cmapss", custom_csv_path: Optional[Path] = None, playback_interval_sec: float = 0.0):
        if custom_csv_path:
            self.log_path = Path(custom_csv_path)
            self.dataset_key = "custom_log"
        else:
            self.log_path = self.DATASET_FILES.get(dataset_key, self.DATASET_FILES["nasa_cmapss"])
            self.dataset_key = dataset_key

        self.interval = playback_interval_sec

    def stream_records(self, limit: Optional[int] = None) -> Generator[str, None, None]:
        """Ingests historical data, dynamically re-anchors timestamps to now, and streams JSON frames."""
        if not self.log_path.exists():
            raise FileNotFoundError(f"Benchmark log not found at: {self.log_path}")

        now = datetime.now(timezone.utc)
        record_count = 0

        with open(self.log_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if limit and record_count >= limit:
                    break

                # Re-anchor historical relative step to active operational timestamp
                ts = (now - timedelta(seconds=(100 - i) * 3)).isoformat()
                
                # Check for fault/anomaly flags across schemas
                is_fault = (
                    row.get("is_fault_state", "").lower() == "true" or
                    "FAULT" in row.get("fault_type", "").upper() or
                    ("FAILURE" in row.get("failure_type", "").upper() and row.get("failure_type") != "NO_FAILURE")
                )

                frame = TelemetryFrame(
                    telemetry_id=f"REPLAY-{self.dataset_key.upper()}-{1000 + i}",
                    device_id=row.get("sensor_id", f"BENCHMARK-UNIT-{i}"),
                    machine_type=row.get("machine_type", "GE_HA_GAS_TURBINE"),
                    facility_location=row.get("facility_location", "GREENVILLE_SC_USA"),
                    timestamp_utc=ts,
                    vibration_rms_g=round(float(row.get("vibration_rms_g", 2.0)), 3),
                    bearing_temp_celsius=round(float(row.get("bearing_temp_c", row.get("bearing_temp_celsius", 95.0))), 2),
                    rotational_speed_rpm=round(float(row.get("rotational_speed_rpm", 3600.0)), 1),
                    power_draw_kw=round(float(row.get("power_draw_kw", 3500.0)), 2),
                    hydraulic_pressure_psi=float(row.get("hydraulic_psi")) if row.get("hydraulic_psi") else None,
                    acoustic_emission_db=float(row.get("acoustic_db")) if row.get("acoustic_db") else None,
                    dataset_source=f"BENCHMARK_{self.dataset_key.upper()}",
                    is_fault_state=is_fault
                )

                payload = json.dumps(asdict(frame))
                yield payload
                record_count += 1

                if self.interval > 0:
                    time.sleep(self.interval)

    def replay_batch_to_dicts(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Parses the historical benchmark records directly into in-memory dictionary batch."""
        return [json.loads(p) for p in self.stream_records(limit=limit)]
