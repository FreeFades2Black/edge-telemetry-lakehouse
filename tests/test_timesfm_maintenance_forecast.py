"""
Multi-Cloud Edge Telemetry & Analytical Lakehouse
Test Suite for TimesFM-3 Predictive Maintenance Forecaster
"""

import pytest
from src.analytics.timesfm_predictive_maintenance import TimesFM3PredictiveMaintenanceForecaster


def test_timesfm_maintenance_forecast_execution():
    """Verify TimesFM-3 generates 30-day degradation trajectories and RUL."""
    forecaster = TimesFM3PredictiveMaintenanceForecaster()
    dossier = forecaster.forecast_machine_degradation_trajectories()

    assert "model_metadata" in dossier
    assert "equipment_predictive_trajectories" in dossier
    assert len(dossier["equipment_predictive_trajectories"]) == 6

    # Verify GEV turbine imminent failure detection
    gev_turb = next(eq for eq in dossier["equipment_predictive_trajectories"] if eq["equipment_id"] == "GEV-TURB-03-GVL")
    assert gev_turb["urgency_classification"] == "CRITICAL_IMMINENT_OUTAGE"
    assert gev_turb["remaining_useful_life_hrs"] < 200
    assert len(gev_turb["30_day_trajectory"]) == 15
