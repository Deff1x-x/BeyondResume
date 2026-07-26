"""Temporary local reproduction for AI Candidate Compare 503 diagnosis.

Not for commit. Does not print API keys.
"""

from __future__ import annotations

import sys
import traceback
from pathlib import Path
from uuid import UUID

from sqlalchemy.orm import Session

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.db.session import SessionLocal  # noqa: E402
from app.models.vacancy import Vacancy  # noqa: E402
from app.services import ai_candidate_compare as service  # noqa: E402
from app.services.ai_candidate_compare import (  # noqa: E402
    AiCandidateCompareUnavailableError,
    clear_ai_candidate_compare_cache,
)


VACANCY_ID = UUID("c3440939-9873-4bac-97b7-9482692efb49")
CANDIDATE_IDS = [
    UUID("fce674d1-3c00-49a0-8e2c-6f496d9c1c92"),
    UUID("c3724659-d902-48e5-8883-98fcbce7febc"),
]


def main() -> None:
    clear_ai_candidate_compare_cache()
    session: Session = SessionLocal()
    try:
        vacancy = session.get(Vacancy, VACANCY_ID)
        if vacancy is None:
            raise SystemExit("vacancy not found in local DB")
        print(
            f"[AI_COMPARE_DIAG] reproduce vacancy={VACANCY_ID} "
            f"employer_id={vacancy.employer_id}",
            flush=True,
        )
        context = service.build_ai_candidate_compare_context(
            session,
            employer_id=vacancy.employer_id,
            vacancy_id=VACANCY_ID,
            candidate_ids=CANDIDATE_IDS,
        )
        print(
            f"[AI_COMPARE_DIAG] context_ok mode={context.generation_mode} "
            f"facts={len(context.fact_ids)} prompt_chars="
            f"{len(service.build_ai_candidate_compare_prompt(context))}",
            flush=True,
        )
        result = service.get_ai_candidate_compare(context)
        print(
            f"[AI_COMPARE_DIAG] SUCCESS mode={result.generation_mode} "
            f"summary_len={len(result.summary)} assessments={len(result.candidate_assessments)}",
            flush=True,
        )
    except AiCandidateCompareUnavailableError as error:
        cause = error.__cause__
        cause_type = type(cause).__name__ if cause is not None else None
        cause_msg = str(cause) if cause is not None else None
        print(
            f"[AI_COMPARE_DIAG] UNAVAILABLE type={type(error).__name__} "
            f"cause={cause_type} cause_msg={cause_msg}",
            flush=True,
        )
        traceback.print_exc()
        raise SystemExit(1) from error
    except Exception:
        traceback.print_exc()
        raise SystemExit(2)
    finally:
        session.close()


if __name__ == "__main__":
    main()
