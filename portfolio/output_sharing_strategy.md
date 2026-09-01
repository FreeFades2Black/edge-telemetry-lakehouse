# Industrial Telemetry Lakehouse: Public Output Sharing Strategy

To showcase your lakehouse outputs publicly without requiring visitors to pull the repo, configure cloud credentials, or spin up Spark clusters, you can use automated GitHub workflows that publish interactive web dashboards, rendered reports, and live status badges directly on your repository.

---

## 🌐 1. Zero-Cost Live Visualizers

### Option A: GitHub Pages + Static HTML Dashboard (Easiest & Most Impactful)
* **How It Works:** A scheduled GitHub Actions workflow runs the pipeline on the historical replay data, generates interactive Plotly/Chart.js HTML charts or a lightweight static web dashboard, and pushes the build artifacts directly to GitHub Pages.
* **Public Deliverable:** A live URL ([`https://FreeFades2Black.github.io/edge-telemetry-lakehouse/`](https://FreeFades2Black.github.io/edge-telemetry-lakehouse/)) linked at the top of your GitHub repository.

### Option B: Automated Streamlit Community Cloud App
* **How It Works:** Point Streamlit Community Cloud at your repository. It reads the historical Gold-layer parquet/JSON tables directly from the repo and provides an interactive UI with sliders, anomaly alerts, and machine health scorecards.
* **Public Deliverable:** A live web application with zero server maintenance.

### Option C: Rendered Jupyter / Quarto Reports
* **How It Works:** Run your PySpark/DuckDB pipeline inside a notebook and execute `quarto render` or `nbconvert` in CI to generate a styled, executive-ready HTML/PDF report attached to each release.

---

## ⚙️ 2. GitHub Action: Automated Daily Run & Dashboard Publisher

```yaml
# FILE: .github/workflows/trail-dashboard-deploy.yml
# LORE: The Gunslinger leaves a clear trail marker at every camp.
#       No traveler questions the path when the maps are drawn in plain sight.

name: "publish-telemetry-dashboard"

on:
  push:
    branches: [ "main" ]
  schedule:
    # Run daily at 06:00 UTC to simulate fresh daily batch scoring
    - cron: "0 6 * * *"
  workflow_dispatch:

permissions:
  contents: write
  pages: write
  id-token: write

jobs:
  run_pipeline_and_publish:
    name: "Execute Replay and Publish Dashboard"
    runs-on: ubuntu-latest
    steps:
      - name: "Draw Iron (Checkout Code)"
        uses: actions/checkout@v4

      - name: "Prime the Cylinder (Setup Python)"
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"

      - name: "Load Cartridges (Install Dependencies)"
        run: pip install pandas pyarrow duckdb pydantic pytest

      - name: "Execute Gold Layer Aggregation"
        run: python src/analytics/generate_gold_metrics.py

      - name: "Build Static Executive Dashboard"
        run: python src/visualization/build_dashboard.py --output-dir dist/

      - name: "Upload GitHub Pages Artifact"
        uses: actions/upload-pages-artifact@v3
        with:
          path: "dist/"

      - name: "Deploy to GitHub Pages"
        id: deployment
        uses: actions/deploy-pages@v4
```

---

## 📊 3. Live Dashboard Embedding Blueprint

```markdown
# 🏭 Edge Telemetry Lakehouse

[![Dashboard Live](https://img.shields.io/badge/Live_Demo-GitHub_Pages-2ea44f?style=for-the-badge&logo=github)](https://FreeFades2Black.github.io/edge-telemetry-lakehouse/)
[![Data Pipeline](https://img.shields.io/github/actions/workflow/status/FreeFades2Black/edge-telemetry-lakehouse/trail-dashboard-deploy.yml?label=Pipeline%20Run&style=for-the-badge)](https://github.com/FreeFades2Black/edge-telemetry-lakehouse/actions)
[![Quality Gate](https://img.shields.io/badge/Data_Quality-100%25_Clean-blue?style=for-the-badge)](https://github.com/FreeFades2Black/edge-telemetry-lakehouse)

> **Live Interactive Executive View:** [Open Fleet Telemetry Scorecard ↗](https://FreeFades2Black.github.io/edge-telemetry-lakehouse/)
```
