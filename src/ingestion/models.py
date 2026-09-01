"""
Multi-Cloud Edge Telemetry & Analytical Lakehouse
Core Data Contracts & Pydantic Validation Models for Industrial Edge IoT.
Target Environments: BMW Manufacturing (Robotics), Michelin (Presses), GE Vernova (Turbines).
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class MachineType(str, Enum):
    GAS_TURBINE_HA = "GE_HA_GAS_TURBINE"
    AMR_ROBOTIC_ARM = "BMW_AMR_ROBOT_KUKA"
    CURING_PRESS = "MICHELIN_CURING_PRESS"
    CNC_MILL_5AXIS = "DMG_MORI_5AXIS_CNC"
    GRID_TRANSFORMER = "DUKE_GRID_TRANSFORMER"


class PlantLocation(str, Enum):
    GREENVILLE_SC = "GREENVILLE_SC_USA"
    GREER_SC = "GREER_SC_USA"
    SPARTANBURG_SC = "SPARTANBURG_SC_USA"
    MUNICH_DE = "MUNICH_DE"
    CLERMONT_FR = "CLERMONT_FERRAND_FR"


class EdgeSensorPayload(BaseModel):
    """Raw telemetry payload transmitted from factory edge gateways (MQTT / OPC-UA / Kinesis)."""

    telemetry_id: str = Field(..., description="Unique UUID for the telemetry event")
    device_id: str = Field(..., description="Unique machine / gateway hardware identifier")
    machine_type: MachineType = Field(..., description="Industrial equipment classification")
    facility_location: PlantLocation = Field(..., description="Manufacturing plant location")
    timestamp_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Sensor Telemetry Metrics
    vibration_rms_g: float = Field(..., ge=0.0, le=50.0, description="Vibration velocity RMS in G-force (0-50 G)")
    bearing_temp_celsius: float = Field(..., ge=-40.0, le=300.0, description="Bearing temperature in Celsius")
    rotational_speed_rpm: float = Field(..., ge=0.0, le=25000.0, description="Rotor / spindle RPM")
    power_draw_kw: float = Field(..., ge=0.0, le=5000.0, description="Active power consumption in kW")
    hydraulic_pressure_psi: Optional[float] = Field(None, ge=0.0, le=10000.0, description="Hydraulic line pressure PSI")
    acoustic_emission_db: Optional[float] = Field(None, ge=0.0, le=160.0, description="Acoustic high-frequency noise dB")

    # Edge Gateway Metadata
    firmware_version: str = Field("v2.4.1", description="Edge agent firmware version")
    network_latency_ms: float = Field(12.5, ge=0.0, description="Edge-to-cloud roundtrip latency")
    is_simulated_anomaly: bool = Field(False, description="Ground truth flag for synthetic validation")

    @field_validator("timestamp_utc", mode="before")
    @classmethod
    def parse_timestamp(cls, value: Any) -> datetime:
        if isinstance(value, str):
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        elif isinstance(value, (int, float)):
            return datetime.fromtimestamp(value, tz=timezone.utc)
        return value


class EnrichedTelemetryRecord(EdgeSensorPayload):
    """Silver layer enriched telemetry with quality score and health indices."""

    quality_score: float = Field(..., ge=0.0, le=100.0, description="Data quality score percentage")
    is_valid: bool = Field(True, description="Passed all Bronze-to-Silver quality rules")
    anomaly_flag: bool = Field(False, description="Statistical anomaly detected")
    anomaly_severity: str = Field("NORMAL", description="NORMAL, WARNING, or CRITICAL")
    anomaly_reasons: list[str] = Field(default_factory=list)
    ingested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
