
import os, asyncio, signal, random, time, shutil, subprocess
from dataclasses import dataclass, field
from typing import Dict, Optional, List

def _env_bool(name: str, default: bool = False) -> bool:
    v = os.environ.get(name)
    if v is None:
        return default
    return v.lower() in ("1", "true", "yes", "on")

USE_DOCKER = _env_bool("USE_DOCKER", True)
DOCKER_BIN = os.environ.get("DOCKER_BIN", "docker")
RASA_IMAGE = os.environ.get("RASA_IMAGE", "rasa/rasa:3.6.20-full")

def _resolve_rasa_bin() -> str:
    rb = os.environ.get("RASA_BIN")
    if rb and os.path.isfile(rb) and os.access(rb, os.X_OK):
        return rb
    rb = shutil.which("rasa")
    if rb:
        return rb
    venv_bin = os.path.join(os.environ.get("VIRTUAL_ENV", ""), "bin", "rasa")
    if venv_bin and os.path.isfile(venv_bin) and os.access(venv_bin, os.X_OK):
        return venv_bin
    raise FileNotFoundError(
        "Rasa não encontrado e USE_DOCKER=0. "
        "Defina RASA_BIN ou habilite USE_DOCKER=1 e RASA_IMAGE."
    )

@dataclass
class RasaProcess:
    project: str
    port: int
    pid: Optional[int] = None
    container_id: Optional[str] = None
    started_at: float = field(default_factory=time.time)

class RasaManager:
    def __init__(self, workspace: str, logs_dir: str):
        self.workspace = os.path.abspath(workspace)
        self.logs_dir = os.path.abspath(logs_dir)
        os.makedirs(self.logs_dir, exist_ok=True)
        self.processes: Dict[str, RasaProcess] = {}
        self.jobs: Dict[str, dict] = {}

    def _project_path(self, name: str) -> str:
        return os.path.join(self.workspace, name)

    def _ensure_project(self, name: str):
        base = self._project_path(name)
        for must in ("config.yml", "domain.yml", "data"):
            if not os.path.exists(os.path.join(base, must)):
                raise FileNotFoundError(f"Project '{name}' missing {must}")

    def list_projects(self) -> List[str]:
        return sorted([d for d in os.listdir(self.workspace)
                       if os.path.isdir(os.path.join(self.workspace, d))])

    def status(self, name: str) -> dict:
        proc = self.processes.get(name)
        return {
            "running": proc is not None,
            "port": proc.port if proc else None,
            "pid": proc.pid if proc else None,
            "container_id": proc.container_id if proc else None,
            "mode": "docker" if USE_DOCKER else "local"
        }

    async def train(self, name: str) -> str:
        self._ensure_project(name)
        job_id = f"train-{name}-{int(time.time())}-{random.randint(1000,9999)}"
        log_path = os.path.join(self.logs_dir, f"{job_id}.log")
        self.jobs[job_id] = {"id": job_id, "project": name, "status": "running", "log_path": log_path}

        base = self._project_path(name)

        if USE_DOCKER:
            # ENTRYPOINT da imagem já é 'rasa'; passe somente subcomandos
            cmd = [
                DOCKER_BIN, "run", "--rm",
                "-v", f"{base}:/app",
                "-w", "/app",
                RASA_IMAGE, "train"
            ]
            cwd = None
        else:
            cmd = [_resolve_rasa_bin(), "train"]
            cwd = base

        with open(log_path, "w") as lf:
            lf.write(f"Mode: {'docker' if USE_DOCKER else 'local'}\n")
            lf.write(f"Project: {base}\n")
            lf.write(f"$ {' '.join(cmd)}\n\n")
            proc = await asyncio.create_subprocess_exec(
                *cmd, cwd=cwd, stdout=lf, stderr=asyncio.subprocess.STDOUT
            )
            rc = await proc.wait()
            self.jobs[job_id]["status"] = "succeeded" if rc == 0 else "failed"
            self.jobs[job_id]["exit_code"] = rc
        return job_id

    async def start_inference(self, name: str, port: Optional[int] = None) -> dict:
        self._ensure_project(name)
        if name in self.processes:
            raise RuntimeError("Already running")

        port = port or random.randint(5005, 5999)
        base = self._project_path(name)

        if USE_DOCKER:
            container_name = f"rasa-{name}"
            cmd = [
                DOCKER_BIN, "run", "-d",
                "--name", container_name,
                "-p", f"{port}:5005",
                "-v", f"{base}:/app",
                "-w", "/app",
                RASA_IMAGE, "run",
                "--enable-api", "--cors", "*",
                "--port", "5005",
                "--model", "models"
            ]
            cp = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            out, err = await cp.communicate()
            if cp.returncode != 0:
                raise RuntimeError(f"docker run failed: {err.decode()}")
            container_id = out.decode().strip()
            await asyncio.sleep(2)
            self.processes[name] = RasaProcess(project=name, port=port, pid=None, container_id=container_id)
            return {"project": name, "port": port, "container_id": container_id}
        else:
            log_path = os.path.join(self.logs_dir, f"rasa-{name}-{port}.log")
            cmd = [_resolve_rasa_bin(), "run", "--enable-api", "--cors", "*",
                   "--port", str(port), "--model", "models"]
            lf = open(log_path, "w")
            proc = await asyncio.create_subprocess_exec(
                *cmd, cwd=base, stdout=lf, stderr=asyncio.subprocess.STDOUT
            )
            await asyncio.sleep(2)
            self.processes[name] = RasaProcess(project=name, port=port, pid=proc.pid)
            return {"project": name, "port": port, "pid": proc.pid}

    async def stop_inference(self, name: str) -> bool:
        proc = self.processes.get(name)
        if not proc:
            return False
        if USE_DOCKER and proc.container_id:
            await asyncio.create_subprocess_exec(DOCKER_BIN, "stop", proc.container_id)
            await asyncio.create_subprocess_exec(DOCKER_BIN, "rm", proc.container_id)
        else:
            try:
                os.kill(proc.pid or 0, signal.SIGTERM)
            except ProcessLookupError:
                pass
        self.processes.pop(name, None)
        return True
