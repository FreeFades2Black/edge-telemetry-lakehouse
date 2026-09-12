# Operational Runbook: Diagnosing MQTT Broker Queue Backpressure & Edge Drops

**Severity:** P2 / Telemetry Ingestion Degraded  
**Target Systems:** Mosquitto MQTT Broker, Telegraf Agent, Delta Bronze Ingest

## Diagnostic Workflow

### 1. Check Broker Queued Messages & Connected Clients
```bash
mosquitto_sub -h localhost -t '$SYS/broker/messages/stored' -C 1
mosquitto_sub -h localhost -t '$SYS/broker/clients/connected' -C 1
```

### 2. Inspect Edge Gateway Offline Disk Spooling
```bash
df -h /var/log/telemetry_spool/
journalctl -u edge-telemetry-collector -n 100 --no-pager | grep -i "spool"
```

### 3. Step-by-Step Remediation
1. If broker memory approaches 80%, increase persistence disk buffer limit:
   ```bash
   sed -i 's/max_queued_messages 1000/max_queued_messages 10000/' /etc/mosquitto/mosquitto.conf
   systemctl reload mosquitto
   ```
2. Trigger forced Bronze pipeline catch-up:
   ```bash
   python -m src.pipeline --drain-spool
   ```
