"""In-memory job registry for the VIL HTTP surface."""

from __future__ import annotations

from datetime import datetime, timezone
import threading
import uuid
from typing import Any, Callable, Dict, List


JobRunner = Callable[[Dict[str, Any]], Dict[str, Any]]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class JobRegistry:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._jobs: Dict[str, Dict[str, Any]] = {}

    def create_job(self, *, kind: str, payload: Dict[str, Any], runner: JobRunner) -> Dict[str, Any]:
        job_id = str(uuid.uuid4())
        job = {
            "job_id": job_id,
            "kind": kind,
            "status": "queued",
            "created_at": _utc_now(),
            "updated_at": _utc_now(),
            "payload": dict(payload),
            "result": None,
            "error": None,
        }
        with self._lock:
            self._jobs[job_id] = job

        thread = threading.Thread(
            target=self._run_job,
            kwargs={"job_id": job_id, "runner": runner, "payload": dict(payload)},
            daemon=True,
        )
        thread.start()
        return self.get_job(job_id)

    def _run_job(self, *, job_id: str, runner: JobRunner, payload: Dict[str, Any]) -> None:
        with self._lock:
            job = self._jobs[job_id]
            job["status"] = "running"
            job["updated_at"] = _utc_now()

        try:
            result = runner(payload)
            final_status = "success" if result.get("status") in {"ok", "success", "local"} else "failed"
            with self._lock:
                job = self._jobs[job_id]
                job["status"] = final_status
                job["updated_at"] = _utc_now()
                job["result"] = result
        except Exception as exc:
            with self._lock:
                job = self._jobs[job_id]
                job["status"] = "failed"
                job["updated_at"] = _utc_now()
                job["error"] = str(exc)

    def get_job(self, job_id: str) -> Dict[str, Any]:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                raise KeyError(job_id)
            return dict(job)

    def list_jobs(self) -> List[Dict[str, Any]]:
        with self._lock:
            jobs = [dict(job) for job in self._jobs.values()]
        jobs.sort(key=lambda item: item["created_at"], reverse=True)
        return jobs


job_registry = JobRegistry()


__all__ = ["JobRegistry", "job_registry"]
