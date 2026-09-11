# 🏭 Industrial Edge IoT Gateway Automation (Ansible)
### *Fleet Provisioning & Telemetry Daemon Lifecycle for BMW, Michelin & GE Vernova Facilities*

[![Ansible Core](https://img.shields.io/badge/Ansible-2.14%2B-red?style=for-the-badge&logo=ansible&logoColor=white)](https://github.com/FreeFades2Black/edge-telemetry-lakehouse)
[![Target OS](https://img.shields.io/badge/OS-Arch%20%7C%20Ubuntu%20%7C%20RHEL-blue?style=for-the-badge&logo=linux&logoColor=white)](https://github.com/FreeFades2Black/edge-telemetry-lakehouse)
[![Quality Gate](https://img.shields.io/badge/Syntax%20Check-Passed-brightgreen?style=for-the-badge&logo=githubactions&logoColor=white)](https://github.com/FreeFades2Black/edge-telemetry-lakehouse)

---

## 🎯 Architectural Overview

In automotive assembly, tire curing, and gas turbine manufacturing, edge gateways installed on industrial IPCs (Beckhoff, Siemens Microbox, OnLogic, or bare-metal Linux nodes) must ingest high-frequency sensor readings (vibration RMS, temperature, RPM, hydraulic pressure, acoustic emission) and reliably forward them to the **Multi-Cloud Analytical Lakehouse**.

This Ansible automation suite deploys, configures, and operates the **Factory Edge IoT Gateway (`roles/edge_iot_gateway`)**:

```mermaid
flowchart TD
    subgraph S_INV["1. Inventory & Plant Grouping"]
        I1["bmw-greer-gw01<br/>(BMW Greer AMR Robots)"]
        I2["mich-gvl-gw01<br/>(Michelin Curing Presses)"]
        I3["gev-gvl-gw01<br/>(GE Vernova HA Turbines)"]
        I4["omarchy<br/>(Arch Linux AI Edge Node)"]
    end

    subgraph S_ROLE["2. roles/edge_iot_gateway"]
        R1["01_prerequisites<br/>User/group & /opt/edge-lakehouse hierarchy"]
        R2["02_collector_install<br/>edge_collector.py daemon deployment"]
        R3["03_configuration<br/>collector.conf & logrotate policies"]
        R4["04_systemd_services<br/>edge-telemetry-collector.service & healthcheck.timer"]
        R5["05_verification<br/>Smoke test & live JSON health query"]
    end

    subgraph S_OS["3. Edge Host Services & Buffers"]
        D1["edge-telemetry-collector.service<br/>(Hardened Non-Root Daemon)"]
        D2["/var/lib/edge-lakehouse/spool<br/>(Offline Store-and-Forward Buffer)"]
        D3["edge-telemetry-healthcheck.timer<br/>(Automated Sentinel Health Audit)"]
    end

    S_INV --> S_ROLE
    S_ROLE --> S_OS
```

---

## 📂 Directory Structure

```text
ansible/
├── ansible.cfg                          # Global Ansible runtime config & SSH multiplexing
├── inventory/
│   ├── hosts.ini                        # Plant inventory (BMW Greer, Michelin, GE Vernova, Omarchy)
│   └── group_vars/
│       ├── all.yml                      # Global lakehouse buffer sizes, intervals & endpoints
│       └── factory_edge_gateways.yml    # Systemd resource quotas & log rotation policies
├── playbooks/
│   ├── site.yml                         # Master fleet deployment entrypoint
│   ├── provision-edge-gateways.yml      # Main role provisioning playbook
│   └── verify-edge-health.yml           # Operational audit & buffer queue health check
└── roles/
    └── edge_iot_gateway/
        ├── defaults/main.yml            # Default ports, paths, and anomaly rates
        ├── handlers/main.yml            # Systemd reloads and service restarts
        ├── meta/main.yml                # Galaxy role metadata and OS compatibility
        ├── tasks/
        │   ├── main.yml                 # Master task router with tags
        │   ├── 01_prerequisites.yml    # Users, groups, and kernel TCP tuning
        │   ├── 02_collector_install.yml # Python executable installation
        │   ├── 03_configuration.yml    # collector.conf & logrotate deployment
        │   ├── 04_systemd_services.yml # Systemd unit & timer lifecycle
        │   └── 05_verification.yml      # Smoke test & assertion gates
        └── templates/
            ├── collector.conf.j2
            ├── edge_collector.py.j2
            ├── edge-telemetry-collector.service.j2
            ├── edge-telemetry-healthcheck.service.j2
            ├── edge-telemetry-healthcheck.timer.j2
            └── edge-lakehouse.logrotate.j2
```

---

## 🚀 Quickstart & Operational Commands

### 1. Syntax Validation
```bash
ansible-playbook -i inventory/hosts.ini playbooks/provision-edge-gateways.yml --syntax-check
ansible-playbook -i inventory/hosts.ini playbooks/verify-edge-health.yml --syntax-check
```

### 2. Dry-Run / Check Mode
```bash
ansible-playbook -i inventory/hosts.ini playbooks/provision-edge-gateways.yml --check
```

### 3. Deploy to Edge Fleet (or Specific Plant)
```bash
# Deploy to entire multi-plant fleet
ansible-playbook -i inventory/hosts.ini playbooks/provision-edge-gateways.yml

# Deploy exclusively to BMW Greer Assembly
ansible-playbook -i inventory/hosts.ini playbooks/provision-edge-gateways.yml --limit greer_plant

# Deploy to Omarchy Edge Node
ansible-playbook -i inventory/hosts.ini playbooks/provision-edge-gateways.yml --limit omarchy_edge
```

### 4. Verify Live Health & Queue Depths
```bash
ansible-playbook -i inventory/hosts.ini playbooks/verify-edge-health.yml
```

---

## 🛡️ Security Hardening & Isolation

The `edge-telemetry-collector.service` systemd unit includes the following isolation directives:
* `User=edge-iot` & `Group=industrial`: Runs without root privileges.
* `NoNewPrivileges=true`: Prevents privilege escalation.
* `ProtectSystem=full`: Mounts `/usr`, `/boot`, and `/etc` read-only for the daemon process.
* `ProtectHome=true`: Completely isolates `/home`, `/root`, and `/run/user`.
* `PrivateTmp=true`: Restricts access to global `/tmp`.
* `MemoryMax=512M` & `CPUQuota=50%`: Prevents runaway memory/CPU consumption on edge IPCs.

---

## 🔄 Store-and-Forward Offline Resilience

When plant WAN connectivity drops, the collector does not drop sensor telemetry frames:
1. Batches are serialized and saved atomically into `/var/lib/edge-lakehouse/spool/`.
2. The healthcheck sentinel monitors `spool_queue_depth` and alerts if buffer exceeds `max_buffer_mb` (default 512 MB).
3. Upon network restoration, spooled frames are transmitted in FIFO order to the Lakehouse Bronze Ingestion endpoint.
