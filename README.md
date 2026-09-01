# ⚡ Multi-Cloud Edge Telemetry & Analytical Lakehouse
### *High-Throughput Industrial IoT Ingestion, Automated Quality Gates & Predictive Anomaly Detection*

[![CI/CD Matrix Quality Gate](https://github.com/FreeFades2Black/edge-telemetry-lakehouse/actions/workflows/ci.yml/badge.svg)](https://github.com/FreeFades2Black/edge-telemetry-lakehouse/actions/workflows/ci.yml)
[![Nightly Synthetic Ingestion](https://github.com/FreeFades2Black/edge-telemetry-lakehouse/actions/workflows/synthetic_injector_cron.yml/badge.svg)](https://github.com/FreeFades2Black/edge-telemetry-lakehouse/actions/workflows/synthetic_injector_cron.yml)
[![PyTest Status](https://img.shields.io/badge/PyTest-100%25%20Passed-brightgreen?style=for-the-badge&logo=pytest&logoColor=white)](https://github.com/FreeFades2Black/edge-telemetry-lakehouse)
[![Target Industry](https://img.shields.io/badge/Audience-BMW%20%7C%20Michelin%20%7C%20GE%20Vernova-amber?style=for-the-badge&logo=industrial-software&logoColor=white)](https://github.com/FreeFades2Black/edge-telemetry-lakehouse)
[![LocalStack Zero-Cost Sandbox](https://img.shields.io/badge/Sandbox-LocalStack%202--Min%20Eval-blue?style=for-the-badge&logo=docker&logoColor=white)](https://github.com/FreeFades2Black/edge-telemetry-lakehouse)

---

## 🎯 Executive Overview & Industry Context

Industrial IoT environments across automotive manufacturing (**BMW Spartanburg AMR Fleets**), tire production (**Michelin MARC Curing Presses**), and energy generation (**GE Vernova HA Gas Turbines**) generate millions of sensor records per second. Unplanned mechanical downtime costs heavy industry over **$50B annually**.

This project provides an enterprise-grade, multi-cloud **Edge Telemetry & Analytical Lakehouse** platform that:
1. **Ingests High-Throughput Edge Sensor Streams** via AWS Kinesis / LocalStack and validates Pydantic data contracts.
2. **Automates Multi-Stage Data Quality Gates** (scoring records 0–100% and isolating corrupt data into quarantine DLQs before Silver promotion).
3. **Applies Statistical Anomaly Detection** combining ISO 10816 vibration standards, acoustic emission cavitation detection, and thermal runaway algorithms.
4. **Maintains a Medallion Delta Lake Architecture** (Bronze $\rightarrow$ Silver $\rightarrow$ Gold) delivering equipment health indices and predictive maintenance schedules.

---

## 🏛️ End-to-End Architecture & Ingress Topology

```mermaid
flowchart TD
    subgraph S1["1. Industrial Edge Gateways (OPC-UA / MQTT)"]
        A1["BMW AMR Robots (Greer, SC)"]
        A2["Michelin Curing Presses (Greenville, SC)"]
        A3["GE Vernova Gas Turbines (Greenville, SC)"]
        A4["5-Axis CNC Mills (Spartanburg, SC)"]
    end

    subgraph S2["2. Ingestion & Micro-Batching (Kinesis / LocalStack)"]
        B1["Kinesis Data Stream (Sharded Edge Ingress)"]
        B2["Serverless Edge Normalizer (Lambda / PySpark)"]
    end

    subgraph S3["3. Medallion Lakehouse & Quality Gate"]
        C1[("Bronze: Raw Sensor Telemetry S3")]
        C2{"Quality Gate (0-100% Score)"}
        C3[("Quarantine DLQ (Malformed/Unphysical)")]
        C4[("Silver: Cleaned & Schema-Enriched")]
        C5["Statistical Anomaly Engine (ISO 10816 & Z-Score)"]
        C6[("Gold: Machine Health Aggregations & OEE")]
    end

    subgraph S4["4. Operations & CI/CD Flywheel"]
        D1["GitHub Actions Matrix Pipeline (Py3.10 / Py3.11)"]
        D2["Nightly Synthetic Telemetry Cron Injector"]
        D3["Infracost Automated Cloud Spend Gate"]
        D4["LocalStack Local 2-Minute Sandbox"]
    end

    S1 --> B1
    B1 --> B2
    B2 --> C1
    C1 --> C2
    C2 -->|Under 70 Pct Quality| C3
    C2 -->|Valid Over 70 Pct| C4
    C4 --> C5
    C5 --> C6
    D1 -.-> C2
    D2 -.-> C1
```

---

## 📐 Mathematical Methodology & ISO Vibration Standards

### 1. Data Quality Gate Formula
Every telemetry frame is audited across physical bounds, temporal clock drift, and schema completeness:

$$\text{Quality Score} = 100 - \sum (\text{Schema Penalties} + \text{Physical Boundary Violations} + \text{Temporal Drift})$$

* Records with $\text{Quality Score} \ge 70.0$ and zero missing required fields are promoted to **Silver**.
* Out-of-bounds readings are quarantined to protect analytical models from false alarms.

### 2. Machine Health Index & Vibration Limits (ISO 10816-3)
The engine scores physical degradation against standard industrial thresholds:

$$\text{Machine Health Index} = \begin{cases} 
100 - \left(\frac{\text{Vibration RMS}}{\text{Warning Limit}} \times 15\right) & \text{if Normal} \\
\max\left(55, 80 - \frac{\text{Vibration RMS}}{\text{Warning Limit}} \times 15\right) & \text{if Warning} \\
\max\left(10, 50 - \frac{\text{Vibration RMS}}{\text{Critical Limit}} \times 20\right) & \text{if Critical}
\end{cases}$$

---

## 🚀 2-Minute Local Sandbox Quickstart

Hiring managers and platform engineers can spin up the full pipeline locally with zero AWS credentials:

```bash
# 1. Clone the repository
git clone https://github.com/FreeFades2Black/edge-telemetry-lakehouse.git
cd edge-telemetry-lakehouse

# 2. Install dependencies & initialize environment
make init

# 3. Execute PyTest test suite (100% pass rate)
make test

# 4. Execute full Bronze ➔ Silver ➔ Gold pipeline locally
make run-local
```

### LocalStack Emulation & Docker Sandbox
```bash
# Spin up LocalStack (Kinesis, S3, Lambda, DynamoDB)
make localstack-up

# Validate Terraform configuration against LocalStack
make plan
```

---

## 🔄 Automated CI/CD Automation Chamber

* **Python Matrix Testing:** Evaluates PySpark data models against Python 3.10 and 3.11 in parallel.
* **Trivy Vulnerability Scan:** Audits filesystem dependencies and Terraform IaC definitions for CVEs.
* **Nightly Cron Ingestion:** Automatically executes synthetic micro-batches nightly at 02:00 UTC to maintain live Gold analytical snapshots.
* **Infracost PR Cost Diff:** Calculates exact infrastructure spend deltas on every pull request.

---

## ⚖️ License & Attribution

* **License:** MIT Open Source
* **Lead Architect:** Free (`FreeFades2Black`)
