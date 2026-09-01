# Industrial Telemetry Data Provenance & Calibration Methodology

In enterprise industrial data engineering, using historical datasets and statistically calibrating telemetry generation against verified engineering benchmarks is standard practice.

This document establishes the **data provenance, calibration formulas, and historical benchmark replay architecture** powering the **Multi-Cloud Edge Telemetry & Analytical Lakehouse**.

---

## 🏛️ 1. Public Industrial & Benchmark Datasets (Direct Replay)

The lakehouse ingestion bus directly supports ingestion from the three globally recognized public predictive maintenance benchmark datasets:

```
+----------------------------------------------------------------------------------------------------+
|                                    HISTORICAL BENCHMARK SUITE                                      |
+------------------------------------+----------------------------------+----------------------------+
| 1. NASA PCoE C-MAPSS Turbofan      | 2. CWRU Bearing Data Center      | 3. UCI AI4I 2020 Dataset   |
| Multi-cycle run-to-failure         | Accelerometer raceway & ball     | 10,000 real-machine failure|
| exhaust gas & core degradation     | vibration fault waveforms        | records across 5 modes     |
+------------------------------------+----------------------------------+----------------------------+
```

### A. NASA Prognostics Center of Excellence (PCoE) Turbofan (C-MAPSS)
* **Dataset Reference:** Commercial Modular Aero-Propulsion System Simulation (C-MAPSS) Run-to-Failure Dataset.
* **Telemetry Channels:** Operating cycles, High-Pressure Compressor (HPC) outlet temperatures, core speeds, fan speeds, fuel flow ratios, and static pressures.
* **Lakehouse Mapping:** Mapped directly to **GE Vernova HA-Class Gas Turbines** operating at 3,600 RPM for power grid synchronization.
* **Benchmark Purpose:** Validates multi-cycle degradation curves and Remaining Useful Life (RUL) estimation.

### B. Case Western Reserve University (CWRU) Bearing Data Center
* **Dataset Reference:** CWRU Deep Groove Ball Bearing Test Stand (12k/48k samples/sec accelerometer feeds).
* **Telemetry Channels:** Motor load (0 to 3 HP), vibration acceleration RMS ($G$), inner raceway faults (0.007" to 0.021"), ball element faults, and outer raceway faults.
* **Lakehouse Mapping:** Mapped to **BMW Spartanburg AMR Robotic Arms (KUKA)** joint bearings and spindle drives.
* **Benchmark Purpose:** Establishes the ground-truth baseline for ISO 10816-3 mechanical vibration severity and high-frequency acoustic cavitation alerts.

### C. AI4I 2020 Predictive Maintenance Dataset (UCI ML Repository)
* **Dataset Reference:** 10,000 synthetic-calibrated real machine operational records.
* **Telemetry Channels:** Air temperature, process temperature, rotational speed, torque, tool wear, heat dissipation failure (HDF), power failure (PWF), and overstrain failure (OSF).
* **Lakehouse Mapping:** Mapped to **Michelin Curing Presses** and **5-Axis Precision CNC Mills**.
* **Benchmark Purpose:** Validates the multi-variable data quality gate and multi-mode mechanical failure classifications.

---

## 📐 2. Statistical Grounding & Calibrated Synthetic Generation

For live streaming simulations where proprietary telemetry cannot be published directly due to export control, ITAR, or non-disclosure restrictions, the stream generator (`stream_producer.py`) is mathematically calibrated against historical equipment logs:

### 1. Baseline Operational Profiles (Healthy State)
* **Nominal Operating Values:** Ingests baseline parameters derived from verified steady-state equipment specifications:
  $$\text{Vibration}(t) \sim \mathcal{N}(\mu_{\text{vib}}, \sigma_{\text{vib}}^2), \quad \text{Temperature}(t) \sim \mathcal{N}(\mu_{\text{temp}}, \sigma_{\text{temp}}^2)$$
* **Temporal Gaussian Noise:** Generates physical micro-variations matching real sensor jitter and line noise while remaining strictly inside ISO 10816-3 Normal bounds ($<2.5G$).

### 2. Historical Failure Signatures (Degradation State)
* **Bearing Degradation Curve:** Models exponential mechanical wear corresponding to CWRU inner raceway fault expansion:
  $$\text{Vibration}_{\text{degraded}}(t) = \mu_{\text{vib}} + \alpha \cdot e^{\beta t} + \epsilon(t)$$
* **Thermal Runaway Profile:** Injects thermal dissipation decay matching UCI AI4I heat dissipation failures when lubrication breaks down.

---

## 🔄 3. Dual-Mode Ingestion Harness Architecture

The platform provides a dual-mode ingestion harness that allows seamless switching between **Live Calibrated Generation** and **Direct Historical Benchmark Playback**:

```
+-------------------------------------------------------------+
|                     Data Source Switch                      |
+-------------------------------------------------------------+
       |                                             |
       v                                             v
[ Real Historical Logs ]                 [ Calibrated Generator ]
  (NASA / CWRU / CSVs)                     (Simulated Stream)
       \                                             /
        \                                           /
         v                                         v
   +-----------------------------------------------------+
   |            Edge Gateway / Kafka Producer            |
   |   (Normalizes timestamps to real-time playback)     |
   +-----------------------------------------------------+
                             |
                             v
               [ Bronze Lakehouse Storage ]
```

* **Historical Replay Harness (`revolver_replay.py`):** Reads historical CSV archives, adjusts historical cycle timestamps relative to `current_time()`, and streams events onto the ingestion bus.
* **Deterministic Seeds:** Using fixed pseudo-random seeds ensures that running the pipeline on identical historical profiles generates reproducible anomaly triggers across all unit and integration tests.

---

## 💻 4. Programmatic Replay Execution

```python
from src.ingestion.revolver_replay import HistoricalTelemetryReplay

# Replay NASA C-MAPSS Turbofan Run-to-Failure Benchmark
nasa_replay = HistoricalTelemetryReplay(dataset_key="nasa_cmapss")
for payload in nasa_replay.stream_records(limit=10):
    print("Ingested Historical Frame:", payload)

# Replay CWRU Bearing Vibration Benchmark
cwru_replay = HistoricalTelemetryReplay(dataset_key="cwru_bearing")
frames = cwru_replay.replay_batch_to_dicts(limit=10)
print(f"Loaded {len(frames)} CWRU bearing vibration frames.")
```
