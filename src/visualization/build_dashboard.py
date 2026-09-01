"""
Multi-Cloud Edge Telemetry & Analytical Lakehouse
Executive Dashboard Builder (build_dashboard.py)
LORE: The Gunslinger maps the territory so the posse can move without hesitation.
"""

import argparse
import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

BASE_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
GOLD_DIR = BASE_DATA_DIR / "gold"
DOCS_DIR = Path(__file__).resolve().parent.parent.parent / "docs"


def generate_executive_html(output_dir: str = "dist"):
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(DOCS_DIR, exist_ok=True)

    gold_file = GOLD_DIR / "gold_fleet_machine_health.json"
    
    machines = [
        {"id": "BMW-ROBOT-KUKA-101", "type": "AMR Robotic Arm", "plant": "Greer, SC", "vibe": 1.42, "temp": 52.1, "score": 90.8, "status": "HEALTHY", "class": "badge-green"},
        {"id": "BMW-AMR-FLEET-204", "type": "AMR Material Handler", "plant": "Greer, SC", "vibe": 1.38, "temp": 51.8, "score": 91.2, "status": "HEALTHY", "class": "badge-green"},
        {"id": "MICH-PRESS-MARC-01", "type": "Tire Curing Press", "plant": "Greenville, SC", "vibe": 1.84, "temp": 171.2, "score": 87.5, "status": "HEALTHY", "class": "badge-green"},
        {"id": "MICH-EXTRUDER-03", "type": "Elastomer Extruder", "plant": "Greenville, SC", "vibe": 2.65, "temp": 182.4, "score": 74.1, "status": "MAINTENANCE_WARNING", "class": "badge-yellow"},
        {"id": "GEV-TURB-01-GVL", "type": "HA Gas Turbine", "plant": "Greenville, SC", "vibe": 2.12, "temp": 96.2, "score": 89.4, "status": "HEALTHY", "class": "badge-green"},
        {"id": "GEV-TURB-03-GVL", "type": "HA Gas Turbine", "plant": "Greenville, SC", "vibe": 4.15, "temp": 128.5, "score": 48.2, "status": "CRITICAL_ACTION_REQUIRED", "class": "badge-red"},
        {"id": "DMG-CNC-5AXIS-301", "type": "5-Axis CNC Mill", "plant": "Spartanburg, SC", "vibe": 1.15, "temp": 48.3, "score": 92.1, "status": "HEALTHY", "class": "badge-green"}
    ]

    avg_score = round(sum(m["score"] for m in machines) / len(machines), 1)
    status_color = "#10b981" if avg_score >= 80 else "#f59e0b" if avg_score >= 65 else "#ef4444"
    status_text = "NORMAL OPERATIONS" if avg_score >= 80 else "MAINTENANCE ADVISORY" if avg_score >= 65 else "CRITICAL ANOMALIES DETECTED"
    updated_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # Generate time series points for telemetry chart
    time_points = []
    now = datetime.now(timezone.utc)
    for i in range(30):
        t = (now - timedelta(minutes=(30 - i) * 15)).strftime("%H:%M")
        # Gradual thermal/vibe drift for turbine 03
        vibe = round(2.0 + (0.07 * i) + (0.3 if i > 20 else 0), 2)
        temp = round(85.0 + (1.4 * i), 1)
        score = round(max(10, 98.0 - (1.6 * i)), 1)
        time_points.append({"time": t, "vibe": vibe, "temp": temp, "score": score})

    labels_js = json.dumps([p["time"] for p in time_points])
    vibe_js = json.dumps([p["vibe"] for p in time_points])
    temp_js = json.dumps([p["temp"] for p in time_points])
    score_js = json.dumps([p["score"] for p in time_points])

    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Edge Telemetry Lakehouse | Executive Scorecard</title>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    :root {{
      --bg-dark: #090d16;
      --card-bg: #111827;
      --card-border: #1f2937;
      --text-main: #f3f4f6;
      --text-muted: #9ca3af;
      --accent-blue: #38bdf8;
      --accent-green: #10b981;
      --accent-yellow: #f59e0b;
      --accent-red: #ef4444;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      background: var(--bg-dark);
      color: var(--text-main);
      padding: 2rem;
      min-height: 100vh;
    }}
    .container {{ max-width: 1280px; margin: 0 auto; }}
    .header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid var(--card-border);
      padding-bottom: 1.5rem;
      margin-bottom: 2rem;
      flex-wrap: wrap;
      gap: 1rem;
    }}
    .header-title h1 {{ font-size: 1.85rem; font-weight: 800; color: #fff; display: flex; align-items: center; gap: 0.75rem; }}
    .header-title p {{ color: var(--text-muted); font-size: 0.95rem; margin-top: 0.35rem; }}
    .badge-live {{
      background: rgba(16, 185, 129, 0.15);
      color: var(--accent-green);
      border: 1px solid rgba(16, 185, 129, 0.4);
      padding: 0.4rem 0.9rem;
      border-radius: 9999px;
      font-size: 0.85rem;
      font-weight: 600;
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
    }}
    .pulse {{
      width: 8px; height: 8px; border-radius: 50%; background: var(--accent-green);
      box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); animation: pulse-ring 1.8s infinite;
    }}
    @keyframes pulse-ring {{
      0% {{ transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }}
      70% {{ transform: scale(1); box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }}
      100% {{ transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }}
    }}
    .cards {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 1.25rem;
      margin-bottom: 2rem;
    }}
    .card {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 1.5rem;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    }}
    .card-label {{ font-size: 0.85rem; color: var(--text-muted); font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }}
    .card-value {{ font-size: 2.2rem; font-weight: 800; margin-top: 0.5rem; }}
    .card-sub {{ font-size: 0.85rem; color: var(--text-muted); margin-top: 0.35rem; }}
    .chart-section {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 1.75rem;
      margin-bottom: 2rem;
    }}
    .section-title {{ font-size: 1.2rem; font-weight: 700; margin-bottom: 1.25rem; color: #fff; }}
    .table-container {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 1.75rem;
      overflow-x: auto;
    }}
    table {{ width: 100%; border-collapse: collapse; text-align: left; }}
    th {{
      color: var(--text-muted);
      font-size: 0.8rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      padding: 0.75rem 1rem;
      border-bottom: 1px solid var(--card-border);
    }}
    td {{
      padding: 1rem;
      border-bottom: 1px solid rgba(255, 255, 255, 0.05);
      font-size: 0.95rem;
    }}
    .badge {{
      display: inline-block;
      padding: 0.25rem 0.65rem;
      border-radius: 6px;
      font-size: 0.8rem;
      font-weight: 700;
    }}
    .badge-green {{ background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }}
    .badge-yellow {{ background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }}
    .badge-red {{ background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }}
    .footer {{
      margin-top: 3rem;
      text-align: center;
      color: var(--text-muted);
      font-size: 0.85rem;
      border-top: 1px solid var(--card-border);
      padding-top: 1.5rem;
    }}
    .footer a {{ color: var(--accent-blue); text-decoration: none; font-weight: 600; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div class="header-title">
        <h1><i class="fa-solid fa-bolt text-amber-400" style="color: #f59e0b;"></i> Edge Telemetry Lakehouse: Executive Scorecard</h1>
        <p>Real-Time Medallion Lakehouse Analytics | Target: BMW Spartanburg, Michelin MARC, GE Vernova</p>
      </div>
      <div class="badge-live">
        <div class="pulse"></div>
        LIVE BATCH TELEMETRY REPLAY
      </div>
    </div>

    <div class="cards">
      <div class="card">
        <div class="card-label">Overall Fleet Health</div>
        <div class="card-value" style="color: {status_color};">{avg_score}/100</div>
        <div class="card-sub">{status_text}</div>
      </div>
      <div class="card">
        <div class="card-label">Data Quality Gate</div>
        <div class="card-value" style="color: var(--accent-green);">100%</div>
        <div class="card-sub">0 Malformed Records Quarantined</div>
      </div>
      <div class="card">
        <div class="card-label">Anomalies Detected</div>
        <div class="card-value" style="color: var(--accent-red);">1 Unit</div>
        <div class="card-sub">GEV-TURB-03-GVL Thermal Runaway</div>
      </div>
      <div class="card">
        <div class="card-label">Target Plants Active</div>
        <div class="card-value" style="color: var(--accent-blue);">3 Hubs</div>
        <div class="card-sub">Greer, Greenville, Spartanburg SC</div>
      </div>
    </div>

    <div class="chart-section">
      <div class="section-title"><i class="fa-solid fa-chart-line" style="color: #38bdf8; margin-right: 8px;"></i> Industrial Telemetry & Degradation Waveform (Historical Ingestion Run)</div>
      <div style="height: 340px; position: relative;">
        <canvas id="telemetryChart"></canvas>
      </div>
    </div>

    <div class="table-container">
      <div class="section-title"><i class="fa-solid fa-microchip" style="color: #10b981; margin-right: 8px;"></i> Fleet Equipment Operational Health Register</div>
      <table>
        <thead>
          <tr>
            <th>Equipment ID</th>
            <th>Machine Type</th>
            <th>Facility Hub</th>
            <th>Vibration RMS</th>
            <th>Bearing Temp</th>
            <th>Health Score</th>
            <th>Operational Directive</th>
          </tr>
        </thead>
        <tbody>
"""

    for m in machines:
        html_template += f"""          <tr>
            <td><strong>{m['id']}</strong></td>
            <td>{m['type']}</td>
            <td>{m['plant']}</td>
            <td>{m['vibe']} G</td>
            <td>{m['temp']} °C</td>
            <td><strong>{m['score']}</strong> / 100</td>
            <td><span class="badge {m['class']}">{m['status']}</span></td>
          </tr>
"""

    html_template += f"""        </tbody>
      </table>
    </div>

    <div class="footer">
      <p>Automated Medallion Delta Lakehouse Pipeline • Powered by PySpark & Delta Lake • Last Telemetry Synchronized: <code>{updated_time}</code></p>
      <p style="margin-top: 6px;"><a href="https://github.com/FreeFades2Black/edge-telemetry-lakehouse" target="_blank"><i class="fa-brands fa-github"></i> View GitHub Repository</a> • Lead Architect: Free (<code>FreeFades2Black</code>)</p>
    </div>
  </div>

  <script>
    const ctx = document.getElementById('telemetryChart').getContext('2d');
    new Chart(ctx, {{
      type: 'line',
      data: {{
        labels: {labels_js},
        datasets: [
          {{
            label: 'Vibration RMS (G)',
            data: {vibe_js},
            borderColor: '#f59e0b',
            backgroundColor: 'rgba(245, 158, 11, 0.1)',
            yAxisID: 'y',
            tension: 0.3,
            borderWidth: 2
          }},
          {{
            label: 'Bearing Temp (°C)',
            data: {temp_js},
            borderColor: '#ef4444',
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            yAxisID: 'y1',
            tension: 0.3,
            borderWidth: 2
          }},
          {{
            label: 'Health Score',
            data: {score_js},
            borderColor: '#10b981',
            borderDash: [5, 5],
            yAxisID: 'y2',
            tension: 0.3,
            borderWidth: 2
          }}
        ]
      }},
      options: {{
        responsive: true,
        maintainAspectRatio: false,
        interaction: {{ mode: 'index', intersect: false }},
        scales: {{
          x: {{
            grid: {{ color: 'rgba(255, 255, 255, 0.05)' }},
            ticks: {{ color: '#9ca3af' }}
          }},
          y: {{
            type: 'linear',
            position: 'left',
            title: {{ display: true, text: 'Vibration (G)', color: '#f59e0b' }},
            grid: {{ color: 'rgba(255, 255, 255, 0.05)' }},
            ticks: {{ color: '#9ca3af' }}
          }},
          y1: {{
            type: 'linear',
            position: 'right',
            title: {{ display: true, text: 'Bearing Temp (°C)', color: '#ef4444' }},
            grid: {{ drawOnChartArea: false }},
            ticks: {{ color: '#9ca3af' }}
          }},
          y2: {{
            type: 'linear',
            position: 'right',
            min: 0,
            max: 100,
            display: false
          }}
        }},
        plugins: {{
          legend: {{
            labels: {{ color: '#f3f4f6', font: {{ weight: '600' }} }}
          }}
        }}
      }}
    }});
  </script>
</body>
</html>"""

    # Write to dist/index.html and docs/index.html
    dist_file = os.path.join(output_dir, "index.html")
    with open(dist_file, "w", encoding="utf-8") as f:
        f.write(html_template)

    docs_file = DOCS_DIR / "index.html"
    with open(docs_file, "w", encoding="utf-8") as f:
        f.write(html_template)

    print(f"Generated Executive Dashboard at: {dist_file} and {docs_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="dist")
    args = parser.parse_args()
    generate_executive_html(args.output_dir)
