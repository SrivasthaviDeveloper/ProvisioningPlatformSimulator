"""Script called by Jenkinsfile to resolve a flow and collect host log files."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import httpx


def main() -> None:
    base_url = os.getenv("PROVISIONING_SIMULATOR_URL", "http://127.0.0.1:8010").rstrip("/")
    application = os.getenv("APPLICATION", "OrderHub")
    error = os.getenv("ERROR_TEXT", "")
    event_time = os.getenv("EVENT_TIME") or None
    order_id = os.getenv("ORDER_ID") or None
    correlation_id = os.getenv("CORRELATION_ID") or None
    username = os.environ["DUMMY_SERVER_USERNAME"]
    password = os.environ["DUMMY_SERVER_PASSWORD"]

    with httpx.Client(timeout=10.0) as client:
        response = client.post(
            f"{base_url}/trace",
            json={"application": application, "error": error, "event_time": event_time,
                  "order_id": order_id, "correlation_id": correlation_id},
        )
        response.raise_for_status()
        evidence: dict[str, Any] = response.json()
        order = evidence["order"]["id"]
        logs: list[dict[str, Any]] = []
        server_access: list[dict[str, str]] = []
        for hop in evidence["trace"]:
            server = hop["server"]
            pulled = client.get(
                f"{base_url}/servers/{server}/logs",
                params={"order_id": order, "correlation_id": correlation_id, "event_time": event_time},
                auth=(username, password),
            )
            pulled.raise_for_status()
            payload = pulled.json()
            logs.extend({**entry, "server": server} for entry in payload["logs"])
            server_access.append({"server": server, "log_file": payload["log_file"],
                                  "authenticated_as": payload["authenticated_as"]})
        evidence["logs"] = logs
        evidence["jenkins"] = {"job": "LogLensAI-Reference-Log-Pull", "result": "SUCCESS",
                               "servers_authenticated": server_access, "log_count": len(logs)}
        Path("reference-logs.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
