from __future__ import annotations
from pathlib import Path
import re
import yaml
from .schemas import TaskSuite
SUITE_DIR = Path(__file__).resolve().parents[2] / "examples" / "task_suites"

def _safe_name(name: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", name): raise ValueError("Suite name may contain only letters, numbers, '_' and '-'")
    return name

def load_suite(name: str) -> TaskSuite:
    path = SUITE_DIR / f"{_safe_name(name)}.yaml"
    if not path.exists(): raise FileNotFoundError(f"Task suite not found: {name}")
    return TaskSuite.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))

def save_suite(name: str, suite: TaskSuite) -> dict:
    safe = _safe_name(name)
    SUITE_DIR.mkdir(parents=True, exist_ok=True)
    path = (SUITE_DIR / f"{safe}.yaml").resolve()
    if path.parent != SUITE_DIR.resolve(): raise ValueError("Invalid suite path")
    path.write_text(yaml.safe_dump(suite.model_dump(mode="json"), sort_keys=False, allow_unicode=True), encoding="utf-8")
    return {"name": safe, "title": suite.name, "description": suite.description, "task_count": len(suite.tasks), "required_capabilities": suite.required_capabilities, "resource_count": len(suite.resources)}

def list_suites() -> list[dict]:
    items = []
    if SUITE_DIR.exists():
        for path in sorted(SUITE_DIR.glob("*.yaml")):
            try:
                suite = TaskSuite.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
                items.append({"name": path.stem, "title": suite.name, "description": suite.description, "task_count": len(suite.tasks), "required_capabilities": suite.required_capabilities, "resource_count": len(suite.resources)})
            except Exception: continue
    return items
