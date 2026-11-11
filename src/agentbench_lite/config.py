from __future__ import annotations
import os
from pathlib import Path

APP_DIR = Path(os.getenv("AGENTBENCH_HOME", ".agentbench"))
APP_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_URL = os.getenv("AGENTBENCH_DATABASE_URL", f"sqlite:///{APP_DIR / 'agentbench.db'}")
MAX_TASKS_PER_RUN = int(os.getenv("AGENTBENCH_MAX_TASKS_PER_RUN", "100"))
CORS_ORIGINS = [
    x.strip()
    for x in os.getenv(
        "AGENTBENCH_CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")
    if x.strip()
]