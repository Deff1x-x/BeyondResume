"""AI interpretation of already computed Skill Passport evidence."""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from hashlib import sha256
import json
from threading import Lock
from time import monotonic

from app.core.config import settings
from app.prompts.ai_hiring_intelligence import PROMPT_VERSION, SYSTEM_RULES
from app.schemas.ai_hiring_intelligence import AiHiringIntelligenceResponse
from app.schemas.skill_passport import SkillPassportResponse
from app.services.ai_match_explanation import get_llm_provider


class HiringIntelligenceUnavailableError(Exception):
    pass


CONTEXT_VERSION = "candidate-hiring-context-v1"
RESPONSE_SCHEMA_VERSION = "ai-hiring-response-v1"
SERVICE_VERSION = "ai-hiring-intelligence-service-v1"
ELIGIBLE_SKILL_CONFIDENCE = 50
MAX_CONTEXT_SKILLS = 20
CACHE_TTL_SECONDS = 300
CACHE_LIMIT = 128


@dataclass(frozen=True, slots=True)
class CandidateHiringContext:
    skills: tuple[dict[str, object], ...]
    evidence_sources: tuple[str, ...]

    def as_payload(self) -> dict[str, object]:
        return {
            "context_version": CONTEXT_VERSION,
            "skills": list(self.skills),
            "evidence_sources": list(self.evidence_sources),
            "eligible_skills": [item["name"] for item in self.skills if item["confidence"] >= ELIGIBLE_SKILL_CONFIDENCE],
        }


class _Cache:
    def __init__(self) -> None:
        self.items: OrderedDict[str, tuple[float, AiHiringIntelligenceResponse]] = OrderedDict()
        self.lock = Lock()

    def get(self, key: str) -> AiHiringIntelligenceResponse | None:
        with self.lock:
            entry = self.items.get(key)
            if entry is not None:
                created_at, value = entry
                if monotonic() - created_at > CACHE_TTL_SECONDS:
                    self.items.pop(key, None)
                    return None
                self.items.move_to_end(key)
                return value
            return None

    def put(self, key: str, value: AiHiringIntelligenceResponse) -> None:
        with self.lock:
            self.items[key] = (monotonic(), value)
            self.items.move_to_end(key)
            while len(self.items) > CACHE_LIMIT:
                self.items.popitem(last=False)

    def clear(self) -> None:
        with self.lock:
            self.items.clear()


_cache = _Cache()


def build_hiring_context(*, candidate_name: str | None, passport: SkillPassportResponse) -> CandidateHiringContext:
    del candidate_name  # Candidate identity is not needed by the AI interpretation layer.
    skills = [
        {
            "name": skill.name,
            "confidence": round(skill.evidence_confidence * 100),
            "evidence_count": skill.evidence_count,
            "github_repositories": [
                {"name": item.repository_name, "evidence_count": item.evidence_count, "confidence": item.repository_confidence}
                for item in skill.github_repositories
            ],
            "sources": sorted({item.source_type for item in skill.evidence}),
        }
        for skill in passport.skills
    ]
    skills.sort(key=lambda item: (-int(item["confidence"]), str(item["name"]).lower()))
    return CandidateHiringContext(
        skills=tuple(skills[:MAX_CONTEXT_SKILLS]),
        evidence_sources=tuple(sorted({source for skill in passport.skills for source in {item.source_type for item in skill.evidence}})),
    )


def build_hiring_prompt(context: CandidateHiringContext) -> str:
    return f"{SYSTEM_RULES}\nINPUT:\n{json.dumps(context.as_payload(), ensure_ascii=False, sort_keys=True)}"


def get_hiring_intelligence(context: CandidateHiringContext) -> AiHiringIntelligenceResponse:
    if not any(int(item["confidence"]) >= ELIGIBLE_SKILL_CONFIDENCE for item in context.skills):
        return AiHiringIntelligenceResponse(
            verdict={
                "technical_interview_recommendation": "insufficient_evidence",
                "confidence": 0,
                "summary": "There is not enough confirmed technical evidence to form a technical interview recommendation.",
                "strengths": [],
                "concerns": ["Add verified technical evidence before generating interview questions."],
            },
            interview_questions=[],
        )
    cache_material = {
        "context": context.as_payload(),
        "prompt_version": PROMPT_VERSION,
        "service_version": SERVICE_VERSION,
        "response_schema_version": RESPONSE_SCHEMA_VERSION,
        "model": settings.llm_model,
    }
    key = sha256(json.dumps(cache_material, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    cached = _cache.get(key)
    if cached is not None:
        return cached
    try:
        content = _mock_response(context) if settings.llm_provider == "mock" else get_llm_provider().generate(build_hiring_prompt(context))
        result = AiHiringIntelligenceResponse.model_validate(_parse_json_object(content))
        _validate_semantics(result, context)
    except Exception as error:
        raise HiringIntelligenceUnavailableError from error
    _cache.put(key, result)
    return result


def _parse_json_object(content: str) -> object:
    normalized = content.strip()
    if normalized.startswith("```"):
        normalized = normalized.split("\n", 1)[1] if "\n" in normalized else ""
        normalized = normalized.rsplit("```", 1)[0].strip()
    return json.loads(normalized)


def _validate_semantics(response: AiHiringIntelligenceResponse, context: CandidateHiringContext) -> None:
    eligible = {str(item["name"]) for item in context.skills if int(item["confidence"]) >= ELIGIBLE_SKILL_CONFIDENCE}
    seen: set[tuple[str, str]] = set()
    for question in response.interview_questions:
        if question.skill not in eligible:
            raise HiringIntelligenceUnavailableError("Question skill is not eligible")
        identity = (question.skill.lower(), question.question.strip().lower())
        if identity in seen:
            raise HiringIntelligenceUnavailableError("Duplicate interview question")
        seen.add(identity)


def _mock_response(context: CandidateHiringContext) -> str:
    eligible = [item for item in context.skills if item["confidence"] >= 50]
    recommendation = "recommended" if eligible else "insufficient_evidence"
    return json.dumps({
        "verdict": {
            "technical_interview_recommendation": recommendation,
            "confidence": min(95, max((item["confidence"] for item in eligible), default=0)),
            "summary": "This assessment interprets the supplied technical evidence only.",
            "strengths": [f"{item['name']} has supporting evidence." for item in eligible[:3]],
            "concerns": [] if eligible else ["No skill has sufficient verified evidence for interview questions."],
        },
        "interview_questions": [
            {"skill": item["name"], "difficulty": "medium", "question": f"Explain a technical decision you made using {item['name']}.", "reason": "The Skill Passport contains sufficient supporting evidence."}
            for item in eligible[:5]
        ],
    })
