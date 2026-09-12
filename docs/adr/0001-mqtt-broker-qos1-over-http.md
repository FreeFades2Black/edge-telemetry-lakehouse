# ADR-0001: MQTT Broker with QoS 1 Persistence vs HTTP REST Ingestion for Edge Telemetry

**Status:** Accepted  
**Date:** 2026-05-18  
**Lead Architect:** William Free Hall (Free) <whall4.wh@gmail.com>

## 1. Context & Operational Challenge
Industrial CNC and telemetry sensors operate across intermittent cellular/industrial WiFi connections. Continuous polling over HTTP REST creates high header overhead and dropped telemetry frames during wireless dropouts.

## 2. Options Considered
* **Option A: HTTP/2 REST Ingestion Endpoint**
  - *Evaluation:* Simple integration, but lacks native broker queuing; temporary disconnection at the edge causes sensors to drop vibration time-series frames or buffer in limited RAM.
* **Option B: Eclipse Mosquitto MQTT Broker with QoS 1 (At Least Once Delivery)**
  - *Evaluation:* Lightweight binary protocol (2-byte header), persistent client session queues, client-side offline disk buffering, and automatic re-delivery upon reconnect.

## 3. Decision & Trade-Off Accepted
We adopted **Option B (MQTT QoS 1)**.  
**Trade-Off Accepted:** Introduces potential duplicate messages on network reconnection; handled downstream in the Silver Delta Lake layer via atomic deduplication (`MERGE INTO ... ON device_id, timestamp`).
