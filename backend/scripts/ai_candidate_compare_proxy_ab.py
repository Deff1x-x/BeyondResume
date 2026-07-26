"""Temporary A/B: direct backend vs Next.js rewrite proxy. Not for commit."""

from __future__ import annotations

import json
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

TOKEN = Path(__file__).with_name("_tmp_token.txt").read_text(encoding="utf-8").strip()
VACANCY = "c3440939-9873-4bac-97b7-9482692efb49"
BODY = json.dumps(
    {
        "candidate_ids": [
            "fce674d1-3c00-49a0-8e2c-6f496d9c1c92",
            "c3724659-d902-48e5-8883-98fcbce7febc",
        ]
    }
).encode("utf-8")
PATH = f"/api/v1/employer/vacancies/{VACANCY}/ai-compare"


def post(label: str, base: str) -> None:
    url = f"{base.rstrip('/')}{PATH}"
    req = Request(
        url,
        data=BODY,
        method="POST",
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    started = time.monotonic()
    try:
        with urlopen(req, timeout=120) as resp:
            raw = resp.read()
            duration_ms = round((time.monotonic() - started) * 1000)
            text = raw.decode("utf-8", errors="replace")
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                data = None
            print(f"[{label}] status={resp.status} duration_ms={duration_ms} bytes={len(raw)}")
            if isinstance(data, dict):
                print(
                    f"[{label}] generation_mode={data.get('generation_mode')} "
                    f"assessments={len(data.get('candidate_assessments') or [])} "
                    f"summary_len={len(str(data.get('summary') or ''))} "
                    f"code={data.get('code')}"
                )
            else:
                print(f"[{label}] body_preview={text[:200]!r}")
    except HTTPError as error:
        duration_ms = round((time.monotonic() - started) * 1000)
        raw = error.read().decode("utf-8", errors="replace")
        print(f"[{label}] status={error.code} duration_ms={duration_ms} body={raw[:400]!r}")
    except URLError as error:
        duration_ms = round((time.monotonic() - started) * 1000)
        reason = getattr(error, "reason", error)
        print(f"[{label}] URLError duration_ms={duration_ms} reason={reason!r}")
    except Exception as error:  # noqa: BLE001
        duration_ms = round((time.monotonic() - started) * 1000)
        print(
            f"[{label}] ERROR duration_ms={duration_ms} "
            f"type={type(error).__name__} msg={error}"
        )


def main() -> None:
    # Clear service cache via in-process import (does not affect live uvicorn cache).
    # Live uvicorn has its own process memory; still useful for scripted service path.
    print("NOTE: live uvicorn has separate in-memory cache; clearing local only.")
    try:
        from app.services.ai_candidate_compare import clear_ai_candidate_compare_cache

        clear_ai_candidate_compare_cache()
    except Exception as error:  # noqa: BLE001
        print(f"local_cache_clear_skipped={type(error).__name__}")

    print("--- A direct backend :8000 ---")
    post("A_direct", "http://127.0.0.1:8000")
    print("--- B via Next.js proxy :3000 ---")
    post("B_proxy", "http://127.0.0.1:3000")


if __name__ == "__main__":
    main()
