# Provisioning Platform Simulator

An independent local repository for the LogLensAI hackathon demo. It simulates Hosted and Premise provisioning, IPSM and ESP integrations, separate server log files, and a Jenkins-compatible local controller.

## Run

Requires Python 3.11+ and the FastAPI dependencies listed in `requirements.txt`.

```powershell
python -m pip install -r requirements.txt
python -m uvicorn simulator:app --reload --port 8010
```

For the complete dashboard + API + Jenkins demo, use `../start-demo.ps1` from the workspace `work` folder; it starts all four services.

Open `http://127.0.0.1:8010/docs` for the dummy-server API and `http://127.0.0.1:8020/docs` for the Jenkins demo controller. `POST /trace` resolves an application/error to a server and microservice path. `GET /servers/{server}/logs` requires the read-only Jenkins service account.

LogLensAI authenticates to the local Jenkins-compatible job endpoint using the demo job token. That job then logs into each dummy server using HTTP Basic and pulls its per-server JSONL log file. The dashboard shows the build number, servers accessed, log file paths, and returned entries. The local controller mirrors Jenkins' `buildWithParameters` job flow; it is a lightweight stand-in for a Jenkins installation, not the Jenkins Java server.

The included `Jenkinsfile` and `jenkins_pipeline.py` are for running the same log-pull job in a real Jenkins installation. Configure a Jenkins credential named `dummy-server-reader` and point `PROVISIONING_SIMULATOR_URL` at the simulator reachable from the agent.

Local-only demo defaults (overridable with environment variables): Jenkins user `loglens-demo` / token `demo-jenkins-token`; dummy server user `jenkins-reader` / password `demo-server-readonly`. These values are intentionally fictional and must not be reused outside the local demo. All hosts, logs, calls, payloads, and accounts are fabricated. No SSH or production system is contacted.
