"""SourceClient: calls the n8n source-adapter webhooks. Sync sources return evidence inline;
async sources (OpenAI DR / Gemini DR / Manus) return a provider_job_id we then poll."""
import time

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from . import config


class SourceClient:
    def __init__(self):
        self._http = httpx.Client(timeout=config.SOURCE_TIMEOUT_S + 10)

    @staticmethod
    def _unwrap(resp):
        """n8n webhook (responseMode=lastNode) may return the node json as a bare object, a list
        of items, or {data:[...]}. Normalize to the single result dict the worker expects."""
        if isinstance(resp, list):
            return resp[0] if resp else {}
        if isinstance(resp, dict) and "evidence" not in resp and isinstance(resp.get("data"), list):
            return resp["data"][0] if resp["data"] else {}
        return resp if isinstance(resp, dict) else {}

    def run(self, source: str, job_id, run_id, payload: dict) -> dict:
        """Returns {status, evidence:[...], cost_usd?, provider_job_id?}."""
        path = config.ADAPTER_PATHS.get(source)
        if not path:
            return {"status": "skipped", "evidence": []}
        body = {"job_id": str(job_id), "run_id": str(run_id), **payload}
        try:
            resp = self._unwrap(self._post(config.N8N_BASE_URL + path, body))
        except Exception as e:  # transport failures after retries, or HTTP status errors
            return {"status": "error", "evidence": [], "error": str(e)}
        if source in config.ASYNC_SOURCES:
            return self._poll(source, run_id, resp)
        return resp or {"status": "error", "evidence": []}

    @retry(
        stop=stop_after_attempt(config.SOURCE_RETRIES + 1),
        wait=wait_exponential(multiplier=30, max=60),
        retry=retry_if_exception_type(httpx.TransportError),
        reraise=True,
    )
    def _post(self, url, body):
        r = self._http.post(url, json=body, headers={"X-Researcher-Secret": config.RESEARCHER_WEBHOOK_SECRET})
        r.raise_for_status()
        return r.json()

    def _poll(self, source, run_id, start_resp):
        start_resp = start_resp or {}
        provider_job_id = start_resp.get("provider_job_id")
        status_path = config.ADAPTER_PATHS.get(f"{source}_status")
        if not provider_job_id or not status_path:
            return start_resp if start_resp.get("evidence") else {"status": "error", "evidence": []}
        url = config.N8N_BASE_URL + status_path
        deadline = time.time() + config.SOURCE_TIMEOUT_S
        while time.time() < deadline:
            time.sleep(config.ASYNC_POLL_INTERVAL_S)
            try:
                r = self._http.post(url, json={"run_id": str(run_id), "provider_job_id": provider_job_id},
                                    headers={"X-Researcher-Secret": config.RESEARCHER_WEBHOOK_SECRET})
                data = self._unwrap(r.json()) if r.status_code == 200 else {}
            except Exception:
                data = {}
            if data.get("status") == "completed":
                return data
        return {"status": "timeout", "evidence": []}
