"""
OCaml Gatekeeper Ingress Client for Edge Telemetry Lakehouse.
Pre-Spark and Pre-Bronze ingress filter guaranteeing zero duplicate records
and quarantining invalid machine payloads.
"""

import json
import logging
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

DEFAULT_QUARANTINE_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "data"
    / "quarantine"
    / "dead_letter_events.jsonl"
)


class GatekeeperClient:
    """Manages continuous interactive streaming with ocaml-event-engine."""

    def __init__(
        self,
        binary_cmd: Optional[List[str]] = None,
        initial_seen: Optional[set] = None,
    ):
        self._seen_ids = set(initial_seen or [])
        self.cmd = binary_cmd or self._detect_engine_cmd()
        self._proc: Optional[subprocess.Popen] = None
        if self.cmd:
            self._start_process()

    def _detect_engine_cmd(self) -> Optional[List[str]]:
        local_bins = [
            os.path.join(os.getcwd(), "bin", "ocaml-event-engine"),
            os.path.join(os.getcwd(), "bin", "ocaml-event-engine.exe"),
            os.path.expanduser("~/.local/bin/ocaml-event-engine"),
        ]
        for b in local_bins:
            if os.path.isfile(b) and os.access(b, os.X_OK):
                return [b]

        which_bin = shutil.which("ocaml-event-engine")
        if which_bin:
            return [which_bin]

        docker_bin = shutil.which("docker")
        if docker_bin:
            try:
                check = subprocess.run(
                    [docker_bin, "version"],
                    capture_output=True,
                    timeout=2,
                    text=True,
                )
                if check.returncode == 0:
                    return [
                        docker_bin,
                        "run",
                        "-i",
                        "--rm",
                        "ghcr.io/freefades2black/ocaml-event-engine:latest",
                    ]
            except Exception:
                pass

        return None

    def _start_process(self):
        try:
            self._proc = subprocess.Popen(
                self.cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
        except (OSError, FileNotFoundError) as e:
            logger.warning(
                f"Could not spawn gatekeeper command {self.cmd}: {e}. "
                "Operating in specification fallback mode."
            )
            self._proc = None

    def evaluate(
        self, event_id: str, timestamp: int, payload: str
    ) -> Tuple[str, str, Optional[str]]:
        """
        Sends an event to ocaml-event-engine and returns (status, id, error).
        Status is one of: 'processed', 'duplicate', 'invalid'.
        """
        if self._proc is None or self._proc.poll() is not None:
            return self._spec_fallback(event_id, timestamp, payload)

        req_json = json.dumps({"id": event_id, "timestamp": timestamp, "payload": payload})
        try:
            assert self._proc.stdin is not None
            assert self._proc.stdout is not None
            self._proc.stdin.write(req_json + "\n")
            self._proc.stdin.flush()

            resp_line = self._proc.stdout.readline()
            if not resp_line:
                return self._spec_fallback(event_id, timestamp, payload)

            resp = json.loads(resp_line.strip())
            status = resp.get("status", "invalid")
            resp_id = resp.get("id", event_id)
            error = resp.get("error")
            return status, resp_id, error
        except (BrokenPipeError, OSError, json.JSONDecodeError) as e:
            logger.error(f"Gatekeeper error: {e}")
            return self._spec_fallback(event_id, timestamp, payload)

    def _spec_fallback(
        self, event_id: str, timestamp: int, payload: str
    ) -> Tuple[str, str, Optional[str]]:
        trimmed_id = event_id.strip() if event_id else ""
        trimmed_payload = payload.strip() if payload else ""

        if not trimmed_id:
            return "invalid", event_id, "Event ID cannot be blank"
        if not trimmed_payload:
            return "invalid", event_id, "Payload cannot be empty"
        if trimmed_id in self._seen_ids:
            return "duplicate", event_id, None

        self._seen_ids.add(trimmed_id)
        return "processed", event_id, None

    def filter_batch(
        self,
        records: List[Dict[str, Any]],
        quarantine_file: Optional[Path] = None,
    ) -> List[Dict[str, Any]]:
        """
        Pipes machine telemetry batch through the Gatekeeper:
        - Drops duplicates immediately.
        - Routes invalid records to quarantine log.
        - Returns validated records ready for Bronze table landing.
        """
        q_path = quarantine_file or DEFAULT_QUARANTINE_PATH
        q_path.parent.mkdir(parents=True, exist_ok=True)
        validated_records: List[Dict[str, Any]] = []

        for record in records:
            eid = str(record.get("telemetry_id") or record.get("id") or "").strip()
            
            # Extract timestamp
            raw_ts = record.get("timestamp_utc") or record.get("timestamp")
            if isinstance(raw_ts, (int, float)):
                ts = int(raw_ts)
            elif isinstance(raw_ts, str):
                try:
                    ts = int(datetime.fromisoformat(raw_ts.replace("Z", "+00:00")).timestamp())
                except (ValueError, TypeError):
                    ts = int(datetime.now(timezone.utc).timestamp())
            else:
                ts = int(datetime.now(timezone.utc).timestamp())

            payload_str = json.dumps(record)
            status, res_id, error = self.evaluate(eid, ts, payload_str)

            if status == "processed":
                validated_records.append(record)
            elif status == "duplicate":
                logger.debug(f"[Gatekeeper] Discarding duplicate telemetry ID: {res_id}")
            elif status == "invalid":
                logger.warning(f"[Gatekeeper] Quarantining invalid record: {res_id} ({error})")
                with open(q_path, "a", encoding="utf-8") as qf:
                    qf.write(
                        json.dumps(
                            {
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                                "error": error or "Validation failed",
                                "record": record,
                            }
                        )
                        + "\n"
                    )

        return validated_records

    def close(self):
        if self._proc and self._proc.poll() is None:
            try:
                if self._proc.stdin:
                    self._proc.stdin.close()
                self._proc.terminate()
                self._proc.wait(timeout=2)
            except Exception:
                pass
