# Incident Post-Mortem: Edge Gateway Clock Drift Causing Ingestion Timestamp Rejection

**Incident Date:** 2026-06-20  
**Impact Duration:** 40 minutes  
**Severity:** SEV-3  
**Root Cause:** An edge gateway CMOS battery failure combined with a blocked NTP port (UDP 123) on an industrial firewall caused edge device clocks to drift 42 minutes into the past. Delta Lake schema constraints rejected historical records outside the 15-minute sliding ingest window.

## Timeline
* **08:00 UTC:** Gateway rebooted following power fluctuation; system time reset to RTC uncalibrated clock (-42 min).
* **08:05 UTC:** MQTT messages ingested into Bronze table with invalid past timestamps.
* **08:14 UTC:** Silver transformation pipeline flagged records as out-of-order and shunted 12,000 frames to quarantine.
* **08:35 UTC:** Incident engineer opened NTP port on local firewall; chrony synchronized gateway time to UTC.
* **08:40 UTC:** Quarantine re-process script executed; missing data backfilled.

## Corrective Actions
1. Configured edge agent to include both hardware device timestamp and gateway ingestion receipt timestamp (`sys_receipt_timestamp`).
2. Added pre-flight chrony time synchronization check in Ansible provisioning role (`ansible/roles/edge_agent`).
