
import os, io, asyncio, json, re
from typing import Optional
import httpx

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import HTMLResponse, FileResponse, PlainTextResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel
from .rasa_manager import RasaManager

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_WORKSPACE = os.path.abspath(os.path.join(BACKEND_DIR, "..", "workspace"))
DEFAULT_LOGS = os.path.abspath(os.path.join(BACKEND_DIR, "..", "logs"))
STATIC_DIR = os.path.join(BACKEND_DIR, "static")
TEMPLATES_DIR = os.path.join(BACKEND_DIR, "templates")

WORKSPACE = os.environ.get("WORKSPACE", DEFAULT_WORKSPACE)
LOGS_DIR = os.environ.get("LOGS_DIR", DEFAULT_LOGS)

os.makedirs(WORKSPACE, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)

app = FastAPI(title="Rasa Mini Framework", version="1.3.0")

# CORS (para segurança caso a UI rode em outra origem)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

manager = RasaManager(workspace=WORKSPACE, logs_dir=LOGS_DIR)

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.get("/version")
def version():
    return {"version": app.version}

@app.get("/api/debug/env")
def debug_env():
    # Ajuda a inspecionar runtime (Docker, imagem, paths)
    return {
        "USE_DOCKER": os.environ.get("USE_DOCKER", ""),
        "RASA_IMAGE": os.environ.get("RASA_IMAGE", ""),
        "DOCKER_BIN": os.environ.get("DOCKER_BIN", ""),
        "WORKSPACE": WORKSPACE,
        "LOGS_DIR": LOGS_DIR,
    }

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    index_path = os.path.join(TEMPLATES_DIR, "index.html")
    if not os.path.exists(index_path):
        return HTMLResponse("<h1>UI not found</h1>", status_code=500)
    return templates.TemplateResponse("index.html", {"request": request})

class CreateProject(BaseModel):
    name: str
    template: Optional[str] = None  # "pt-basic" opcional

@app.get("/api/projects")
def list_projects():
    try:
        return {"projects": manager.list_projects()}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/api/projects")
def create_project(payload: CreateProject):
    try:
        name = payload.name.strip()
        if not re.fullmatch(r"[a-zA-Z0-9_-]{1,64}", name):
            raise HTTPException(400, "Invalid project name")
        base = os.path.join(WORKSPACE, name)
        if os.path.exists(base):
            raise HTTPException(400, "Project already exists")
        os.makedirs(base, exist_ok=True)

        minimal = {
            "config.yml": "language: en\npipeline: []\npolicies: []\n",
            "domain.yml": "version: '3.1'\nintents: []\nresponses: {}\n",
            "data/nlu.yml": "version: '3.1'\nnlu: []\n",
            "data/stories.yml": "version: '3.1'\nstories: []\n",
            "data/rules.yml": "version: '3.1'\nrules: []\n",
        }

        tpl_dir = os.path.join(WORKSPACE, "pt-basic-bot") if (payload.template or "").lower() == "pt-basic" else None
        if tpl_dir and os.path.isdir(tpl_dir) and os.path.exists(os.path.join(tpl_dir, "config.yml")):
            for root, dirs, files in os.walk(tpl_dir):
                for f in files:
                    src = os.path.join(root, f)
                    rel = os.path.relpath(src, tpl_dir)
                    dst = os.path.join(base, rel)
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    with open(src, "rb") as rf, open(dst, "wb") as wf:
                        wf.write(rf.read())
        else:
            for rel, content in minimal.items():
                p = os.path.join(base, rel)
                os.makedirs(os.path.dirname(p), exist_ok=True)
                with open(p, "w") as f:
                    f.write(content)
        return {"created": name}
    except HTTPException as he:
        raise he
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/projects/{name}/tree")
def project_tree(name: str):
    base = os.path.join(WORKSPACE, name)
    if not os.path.isdir(base):
        raise HTTPException(404, "project not found")
    files = []
    for root, _, fs in os.walk(base):
        for f in fs:
            rel = os.path.relpath(os.path.join(root, f), base)
            files.append(rel)
    return {"files": sorted(files)}

@app.get("/api/projects/{name}/file")
def get_file(name: str, path: str = Query(...)):
    base = os.path.join(WORKSPACE, name)
    full = os.path.normpath(os.path.join(base, path))
    if not full.startswith(base):
        raise HTTPException(400, "bad path")
    if not os.path.exists(full):
        raise HTTPException(404, "not found")
    with open(full, "r", encoding="utf-8", errors="ignore") as f:
        return PlainTextResponse(f.read())

@app.post("/api/projects/{name}/file")
async def put_file(name: str, path: str = Form(...), content: UploadFile = File(...)):
    base = os.path.join(WORKSPACE, name)
    full = os.path.normpath(os.path.join(base, path))
    if not full.startswith(base):
        raise HTTPException(400, "bad path")
    os.makedirs(os.path.dirname(full), exist_ok=True)
    data = await content.read()
    with open(full, "wb") as f:
        f.write(data)
    return {"saved": path, "bytes": len(data)}

@app.delete("/api/projects/{name}/file")
def delete_file(name: str, path: str = Query(...)):
    base = os.path.join(WORKSPACE, name)
    full = os.path.normpath(os.path.join(base, path))
    if not full.startswith(base):
        raise HTTPException(400, "bad path")
    if os.path.isdir(full):
        raise HTTPException(400, "refusing to delete directory")
    if os.path.exists(full):
        os.remove(full)
        return {"deleted": path}
    raise HTTPException(404, "not found")

@app.get("/api/projects/{name}/status")
def proj_status(name: str):
    return manager.status(name)

@app.post("/api/projects/{name}/train")
async def train(name: str):
    job_id = await manager.train(name)
    return {"job_id": job_id}

@app.get("/api/jobs/{job_id}/logs")
def job_logs(job_id: str):
    log_path = os.path.join(LOGS_DIR, f"{job_id}.log")
    if not os.path.exists(log_path):
        raise HTTPException(404, "log not found")
    return FileResponse(log_path, media_type="text/plain")

class StartPayload(BaseModel):
    port: Optional[int] = None

@app.post("/api/projects/{name}/inference/start")
async def start_inference(name: str, payload: StartPayload):
    return await manager.start_inference(name, port=payload.port)

@app.post("/api/projects/{name}/inference/stop")
async def stop_inference(name: str):
    ok = await manager.stop_inference(name)
    return {"stopped": ok}

class ChatPayload(BaseModel):
    message: str
    sender: str = "user"

@app.post("/api/projects/{name}/chat")
async def chat(name: str, payload: ChatPayload):
    s = manager.status(name)
    if not s.get("running"):
        raise HTTPException(400, "inference not running")
    url = f"http://127.0.0.1:{s['port']}/webhooks/rest/webhook"
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(url, json={"sender": payload.sender, "message": payload.message})
        r.raise_for_status()
        return r.json()
