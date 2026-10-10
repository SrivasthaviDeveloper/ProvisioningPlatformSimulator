"""Local Jenkins-compatible controller for the self-contained hackathon demo.

The controller authenticates LogLensAI, resolves the app trace, then logs into
each dummy server using its read-only demo account to collect JSONL evidence.
It mirrors the Jenkins job/buildWithParameters flow without requiring Java or
a separately installed Jenkins instance.
"""
from __future__ import annotations

import os
import secrets
from datetime import datetime, timezone
from threading import Lock
from typing import Any

import httpx
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.security import HTTPBasic, HTTPBasicCredentials

app = FastAPI(
    title="Jenkins Local Demo Controller",
    version="1.0.0",
    description="A Jenkins-compatible local job endpoint that authenticates to fictional log hosts.",
)
jenkins_basic_auth = HTTPBasic()
build_lock = Lock()
build_number = 0


def authenticate_loglens(credentials: HTTPBasicCredentials = Depends(jenkins_basic_auth)) -> str:
    expected_user = os.getenv("JENKINS_DEMO_USERNAME", "loglens-demo")
    expected_token = os.getenv("JENKINS_DEMO_TOKEN", "demo-jenkins-token")
    valid_user = secrets.compare_digest(credentials.username, expected_user)
    valid_token = secrets.compare_digest(credentials.password, expected_token)
    if not (valid_user and valid_token):
        raise HTTPException(status_code=401, detail="Jenkins demo authentication failed",
                            headers={"WWW-Authenticate": "Basic"})
    return credentials.username


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "engine": "Jenkins-compatible local demo controller"}


@app.get("/api/json")
def jenkins_api(authenticated_as: str = Depends(authenticate_loglens)) -> dict[str, Any]:
    return {"mode": "local-demo", "authenticated_as": authenticated_as,
            "jobs": ["LogLensAI-Reference-Log-Pull"]}


@app.post("/job/LogLensAI-Reference-Log-Pull/buildWithParameters")
def run_reference_log_job(
    application: str = Query(min_length=1, max_length=100),
    error: str = Query(min_length=1, max_length=2000),
    event_time: str | None = None,
    order_id: str | None = None,
    correlation_id: str | None = None,
    authenticated_as: str = Depends(authenticate_loglens),
) -> dict[str, Any]:
    """Run one synchronous demo job and return the archived log evidence."""
    global build_number
    with build_lock:
        build_number += 1
        current_build = build_number

    simulator_url = os.getenv("PROVISIONING_SIMULATOR_URL", "http://127.0.0.1:8010").rstrip("/")
    server_user = os.getenv("DUMMY_SERVER_USERNAME", "jenkins-reader")
    server_password = os.getenv("DUMMY_SERVER_PASSWORD", "demo-server-readonly")
    try:
        trace_response = httpx.post(
            f"{simulator_url}/trace",
            json={"application": application, "error": error, "event_time": event_time,
                  "order_id": order_id, "correlation_id": correlation_id},
            timeout=5.0,
        )
        trace_response.raise_for_status()
        evidence = trace_response.json()
        pulled_logs: list[dict[str, Any]] = []
        pulled_files: list[str] = []
        authenticated_servers: list[str] = []
        selected_order = evidence["order"]["id"]
        selected_correlation = correlation_id
        if not selected_correlation:
            selected_correlation = next(
                (hop.get("correlation_id") for hop in evidence.get("trace", []) if hop.get("correlation_id")),
                None,
            )
        for hop in evidence.get("trace", []):
            server = hop["server"]
            response = httpx.get(
                f"{simulator_url}/servers/{server}/logs",
                params={"order_id": selected_order, "correlation_id": selected_correlation,
                        "event_time": event_time},
                auth=(server_user, server_password),
                timeout=5.0,
            )
            response.raise_for_status()
            server_evidence = response.json()
            pulled_files.append(server_evidence["log_file"])
            authenticated_servers.append(server_evidence["server"])
            pulled_logs.extend({**entry, "server": server} for entry in server_evidence["logs"])
        evidence["logs"] = pulled_logs
        evidence["jenkins"] = {
            "job": "LogLensAI-Reference-Log-Pull",
            "build_number": current_build,
            "result": "SUCCESS",
            "authenticated_as": authenticated_as,
            "server_login_method": "HTTP Basic (read-only demo account)",
            "server_authenticated_as": server_user,
            "servers_authenticated": authenticated_servers,
            "server_count": len(authenticated_servers),
            "log_count": len(pulled_logs),
            "log_files": pulled_files,
            "completed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        return evidence
    except (httpx.HTTPError, KeyError, ValueError):
        raise HTTPException(status_code=502,
                            detail="Jenkins demo job could not retrieve the dummy server reference logs") from None
