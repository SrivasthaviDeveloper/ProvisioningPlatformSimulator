# Provisioning Platform Simulator

An independent, local-only repository that provides realistic fictional order flows for the LogLensAI hackathon demo. It simulates Hosted and Premise provisioning and the IPSM (IP allocation) and ESP (credential) integrations.

## Run

Requires Python 3.11+ and the FastAPI dependencies listed in `requirements.txt`.

```powershell
python -m pip install -r requirements.txt
python -m uvicorn simulator:app --reload --port 8010
```

Open `http://127.0.0.1:8010/docs` for the simulator API. `POST /trace` accepts an application, error, and optional event time or order ID. `GET /health` checks the simulator.

All hosts, logs, integration calls, and payloads are fictional fixtures. The API does not connect to infrastructure or accept credentials.
