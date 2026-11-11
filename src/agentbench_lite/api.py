from __future__ import annotations
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
import httpx
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from . import __version__
from .config import CORS_ORIGINS
from .database import init_db, get_session
from .models import Agent, Evaluation, CaseResult
from .schemas import AgentCreate, AgentUpdate, RunRequest, TaskSuite
from .service import create_evaluation, evaluation_detail, check_compatibility
from .suites import list_suites, load_suite, save_suite
from .agents import REGISTRY, describe_protocol, discover_http_agent, test_http_agent

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db(); yield
app = FastAPI(title="AgentBench Lite API", version=__version__, description="Local-first universal AI agent evaluation workbench", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/api/health")
def health(): return {"status": "ok", "version": __version__, "protocol_version": "1.0"}
@app.get("/api/protocol")
def protocol(): return describe_protocol()
@app.get("/api/agents/registry")
def registry(): return {"entrypoints": sorted(REGISTRY)}
@app.post("/api/agents/discover")
def discover_agent(body: dict):
    endpoint = str(body.get("endpoint", "")).strip()
    if not endpoint: raise HTTPException(400, "Endpoint is required")
    try: return discover_http_agent(endpoint, float(body.get("timeout", 5)))
    except (ValueError, httpx.HTTPError) as exc: raise HTTPException(400, str(exc)) from exc

@app.post("/api/agents/test-connection")
def test_agent_connection(body: dict):
    endpoint = str(body.get("endpoint", "")).strip()
    if not endpoint: raise HTTPException(400, "Endpoint is required")
    try: return test_http_agent(endpoint, float(body.get("timeout", 5)))
    except (ValueError, httpx.HTTPError) as exc: raise HTTPException(400, str(exc)) from exc

@app.get("/api/agents")
def agents(session: Session = Depends(get_session)): return session.exec(select(Agent).order_by(Agent.created_at.desc())).all()
@app.post("/api/agents", status_code=201)
def create_agent(body: AgentCreate, session: Session = Depends(get_session)):
    if body.entrypoint not in REGISTRY: raise HTTPException(400, f"Unknown entrypoint. Available: {', '.join(sorted(REGISTRY))}")
    agent = Agent(**body.model_dump()); session.add(agent); session.commit(); session.refresh(agent); return agent
@app.patch("/api/agents/{agent_id}")
def update_agent(agent_id: str, body: AgentUpdate, session: Session = Depends(get_session)):
    agent = session.get(Agent, agent_id)
    if not agent: raise HTTPException(404, "Agent not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        if value is not None: setattr(agent, key, value)
    session.add(agent); session.commit(); session.refresh(agent); return agent

@app.delete("/api/agents/{agent_id}", status_code=204)
def delete_agent(agent_id: str, session: Session = Depends(get_session)):
    agent = session.get(Agent, agent_id)
    if not agent: raise HTTPException(404, "Agent not found")
    session.delete(agent); session.commit()
@app.get("/api/suites")
def suites(): return list_suites()
@app.get("/api/suites/{suite_name}")
def get_suite(suite_name: str):
    try: return load_suite(suite_name)
    except FileNotFoundError as exc: raise HTTPException(404, str(exc)) from exc
@app.post("/api/suites", status_code=201)
def create_suite(body: TaskSuite, name: str):
    try: return save_suite(name, body)
    except ValueError as exc: raise HTTPException(400, str(exc)) from exc
@app.post("/api/compatibility")
def compatibility(body: dict, session: Session = Depends(get_session)):
    suite_name = str(body.get("suite_name", "")).strip()
    agent_ids = body.get("agent_ids", [])
    if not suite_name: raise HTTPException(400, "suite_name is required")
    if not isinstance(agent_ids, list) or not all(isinstance(x, str) for x in agent_ids): raise HTTPException(400, "agent_ids must be a list of strings")
    try: return check_compatibility(session, agent_ids, suite_name)
    except FileNotFoundError as exc: raise HTTPException(404, str(exc)) from exc

@app.post("/api/evaluations", status_code=201)
def run_evaluation(body: RunRequest, session: Session = Depends(get_session)):
    try: return create_evaluation(session, body)
    except (ValueError, FileNotFoundError) as exc: raise HTTPException(400, str(exc)) from exc
@app.get("/api/evaluations")
def evaluations(session: Session = Depends(get_session)): return session.exec(select(Evaluation).order_by(Evaluation.created_at.desc())).all()
@app.get("/api/evaluations/{evaluation_id}")
def get_evaluation(evaluation_id: str, session: Session = Depends(get_session)):
    try: return evaluation_detail(session, evaluation_id)
    except ValueError as exc: raise HTTPException(404, str(exc)) from exc
@app.get("/api/evaluations/{evaluation_id}/results/{result_id}")
def get_result(evaluation_id: str, result_id: str, session: Session = Depends(get_session)):
    row = session.get(CaseResult, result_id)
    if not row or row.evaluation_id != evaluation_id: raise HTTPException(404, "Result not found")
    return row
