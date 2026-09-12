# ADR-0002: Google TimesFM Foundation Model for Remaining Useful Life (RUL) Prediction

**Status:** Accepted  
**Date:** 2026-06-11  
**Lead Architect:** William Free Hall (Free) <whall4.wh@gmail.com>

## 1. Context & Operational Challenge
Predicting mechanical bearing failure from high-frequency vibration telemetry (accelerometer RMS values) requires identifying non-stationary degradation trends across hundreds of distinct machine types.

## 2. Options Considered
* **Option A: Static Threshold Alarms (e.g. RMS > 4.5 mm/s)**
  - *Evaluation:* Trivial to implement, but provides zero early warning; by the time static thresholds trigger, bearing catastrophic failure occurs within minutes.
* **Option B: Google TimesFM Zero-Shot Multi-Horizon Time Series Model**
  - *Evaluation:* Forecasts 72-hour future degradation curves without requiring per-machine model retraining; accurately detects harmonic resonance anomalies before physical wear occurs.

## 3. Decision & Trade-Off Accepted
We adopted **Option B (TimesFM)**.  
**Trade-Off Accepted:** Batch GPU inference cost (~$45/mo); predictions cached in Gold Delta tables on a rolling 6-hour cycle.
