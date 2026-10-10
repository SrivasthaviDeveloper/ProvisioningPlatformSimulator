"""Fictional provisioning services and captured request/response evidence."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="Provisioning Platform Simulator", version="1.0.0",
              description="Fictional Hosted/Premise order traces and downstream IPSM/ESP evidence.")

FLOWS: list[dict[str, Any]] = [
    {
        "application": "OrderHub", "order_type": "Hosted", "order_id": "ORD-48291",
        "error_terms": ["ip", "address", "allocation", "ipsm", "pool", "409"],
        "server": "hosted-order-srv-01", "microservice": "hosted-order-orchestrator",
        "downstream": "IPSM", "downstream_service": "ip-allocation-service", "status": "FAILED",
        "cause": "IPSM returned IP_POOL_EXHAUSTED for the requested hosted subnet. The order orchestrator propagated HTTP 409 without an allocated address.",
        "request": {"method": "POST", "path": "/v1/hosted/orders/ORD-48291/provision", "headers": {"x-correlation-id": "corr-hosted-48291", "content-type": "application/json"}, "body": {"orderId": "ORD-48291", "tenantId": "TEN-2204", "region": "us-east-demo-1", "service": "edge-connectivity", "ipPool": "172.24.18.0/24"}},
        "response": {"status": 409, "body": {"code": "IP_POOL_EXHAUSTED", "message": "No free addresses in requested demo pool", "correlationId": "corr-hosted-48291"}},
        "downstream_request": {"method": "POST", "path": "/ipsm/v2/allocations", "body": {"orderId": "ORD-48291", "pool": "172.24.18.0/24", "requester": "hosted-order-orchestrator"}},
        "downstream_response": {"status": 409, "body": {"code": "IP_POOL_EXHAUSTED", "available": 0}},
        "logs": ["10:42:11.201 INFO hosted-order-orchestrator accepted order ORD-48291", "10:42:11.238 INFO ip-allocation-service pool=172.24.18.0/24 free=0", "10:42:11.241 ERROR hosted-order-orchestrator downstream IPSM status=409 code=IP_POOL_EXHAUSTED", "10:42:11.244 WARN order-api returned 409 correlation=corr-hosted-48291"],
        "checks": ["Confirm the requested subnet has capacity in IPSM.", "Check whether the order should use an alternate approved pool.", "Retry only after capacity is restored; the order was not provisioned."],
    },
    {
        "application": "OrderHub", "order_type": "Premise", "order_id": "ORD-73106",
        "error_terms": ["credential", "unauthorized", "401", "esp", "token", "auth"],
        "server": "premise-order-srv-02", "microservice": "premise-site-agent", "downstream": "ESP", "downstream_service": "credential-broker", "status": "FAILED",
        "cause": "ESP rejected the premise site's service identity because its demo token audience did not match the premise provisioning API. The site agent returned HTTP 401.",
        "request": {"method": "POST", "path": "/v1/premise/orders/ORD-73106/activate", "headers": {"x-correlation-id": "corr-prem-73106", "content-type": "application/json"}, "body": {"orderId": "ORD-73106", "siteId": "SITE-0198", "device": "CPE-DEMO-044", "profile": "premise-standard"}},
        "response": {"status": 401, "body": {"code": "DOWNSTREAM_AUTH_REJECTED", "message": "Credential broker rejected service identity", "correlationId": "corr-prem-73106"}},
        "downstream_request": {"method": "POST", "path": "/esp/v1/token/validate", "body": {"clientId": "premise-site-agent-demo", "audience": "hosted-provisioning-demo", "scope": "site:activate"}},
        "downstream_response": {"status": 401, "body": {"code": "INVALID_AUDIENCE", "expectedAudience": "premise-provisioning-demo"}},
        "logs": ["11:08:40.004 INFO premise-site-agent received activation order ORD-73106", "11:08:40.019 INFO credential-broker validating demo service identity", "11:08:40.024 ERROR credential-broker INVALID_AUDIENCE expected=premise-provisioning-demo", "11:08:40.027 WARN premise-site-agent activation rejected status=401 correlation=corr-prem-73106"],
        "checks": ["Compare the configured audience with the premise provisioning target.", "Verify the non-secret service identity and scope mapping in ESP.", "Rotate or reissue demo credentials only through the approved identity workflow; never paste secrets into the demo."],
    },
    {
        "application": "OrderHub", "order_type": "Hosted", "order_id": "ORD-59012",
        "error_terms": ["timeout", "timed out", "504", "deadline", "slow"],
        "server": "hosted-order-srv-03", "microservice": "hosted-order-orchestrator", "downstream": "IPSM", "downstream_service": "ip-allocation-service", "status": "DEGRADED",
        "cause": "The orchestration request timed out while waiting on the simulated IPSM allocation call. Evidence shows IPSM responded after the caller's 2-second deadline.",
        "request": {"method": "POST", "path": "/v1/hosted/orders/ORD-59012/provision", "headers": {"x-correlation-id": "corr-hosted-59012", "x-timeout-ms": "2000"}, "body": {"orderId": "ORD-59012", "tenantId": "TEN-4470", "region": "eu-demo-1", "ipPool": "10.88.4.0/24"}},
        "response": {"status": 504, "body": {"code": "DOWNSTREAM_TIMEOUT", "dependency": "IPSM", "deadlineMs": 2000, "correlationId": "corr-hosted-59012"}},
        "downstream_request": {"method": "POST", "path": "/ipsm/v2/allocations", "body": {"orderId": "ORD-59012", "pool": "10.88.4.0/24"}},
        "downstream_response": {"status": 200, "durationMs": 2438, "body": {"code": "ALLOCATED", "address": "10.88.4.27"}},
        "logs": ["12:15:02.110 INFO hosted-order-orchestrator accepted order ORD-59012", "12:15:02.128 INFO ip-allocation-service allocation started", "12:15:04.111 ERROR hosted-order-orchestrator deadline exceeded waiting for IPSM (2000ms)", "12:15:04.566 INFO ip-allocation-service allocation completed duration=2438ms address=10.88.4.27"],
        "checks": ["Check IPSM latency against the 2000 ms orchestration deadline.", "Reconcile the late successful allocation before retrying to avoid duplicate reservations.", "Review retry and idempotency handling for this order ID."],
    },
]

class TraceRequest(BaseModel):
    application: str = Field(min_length=1, max_length=100)
    error: str = Field(min_length=1, max_length=2000)
    event_time: str | None = None
    order_id: str | None = None

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "mode": "fictional simulator"}

@app.get("/applications")
def applications() -> dict[str, Any]:
    return {"applications": ["OrderHub", "IPSM", "ESP"], "order_types": ["Hosted", "Premise"]}

@app.post("/trace")
def trace(request: TraceRequest) -> dict[str, Any]:
    text = request.error.lower()
    candidates = [f for f in FLOWS if request.application.lower() in
                  (f["application"].lower(), f["downstream"].lower())]
    if request.order_id:
        candidates.sort(key=lambda f: f["order_id"].lower() != request.order_id.lower())
    ranked = sorted(candidates, key=lambda f: sum(term in text for term in f["error_terms"]), reverse=True)
    flow = ranked[0] if ranked else FLOWS[0]
    confidence = "high" if sum(term in text for term in flow["error_terms"]) >= 2 else "medium"
    return {
        "simulated": True, "captured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "input": request.model_dump(), "confidence": confidence,
        "order": {"id": flow["order_id"], "type": flow["order_type"], "status": flow["status"]},
        "trace": [
            {"application": "OrderHub", "server": flow["server"], "microservice": flow["microservice"], "role": "order orchestration"},
            {"application": flow["downstream"], "server": f"{flow['downstream'].lower()}-integration-srv-01", "microservice": flow["downstream_service"], "role": "downstream dependency"},
        ],
        "analysis": flow["cause"], "checks": flow["checks"],
        "request": flow["request"], "response": flow["response"],
        "downstream_request": flow["downstream_request"], "downstream_response": flow["downstream_response"],
        "logs": flow["logs"], "event_time_note": f"Event time supplied: {request.event_time}" if request.event_time else "No event time supplied; selected the closest matching fictional flow.",
    }
