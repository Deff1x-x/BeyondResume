from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

from app.services import candidate_vacancies
from app.services.candidate_vacancies import CandidateVacancyMatch
from app.services.matching import MatchResult, SkillGroupBreakdown


def test_list_candidate_vacancies_sorts_by_match_and_keeps_database_order_for_ties(
    monkeypatch,
) -> None:
    recent_tie = SimpleNamespace(id=uuid4(), title="Recent tie")
    older_tie = SimpleNamespace(id=uuid4(), title="Older tie")
    strongest = SimpleNamespace(id=uuid4(), title="Strongest")
    rows = [(recent_tie, "Acme"), (older_tie, "Acme"), (strongest, "Acme")]
    session = Mock()
    session.execute.return_value.all.return_value = rows
    monkeypatch.setattr(candidate_vacancies, "build_passport", lambda *_args: object())

    scores = {recent_tie.id: 50, older_tie.id: 50, strongest.id: 90}

    def build_match(_session, _passport, vacancy, company_name):
        return CandidateVacancyMatch(
            vacancy=vacancy,
            company_name=company_name,
            required_skills=(),
            preferred_skills=(),
            match=MatchResult(
                score=scores[vacancy.id],
                required=SkillGroupBreakdown(matched=(), missing=()),
                preferred=SkillGroupBreakdown(matched=(), missing=()),
            ),
        )

    monkeypatch.setattr(candidate_vacancies, "_build_candidate_vacancy_match", build_match)

    result = candidate_vacancies.list_candidate_vacancies(session, uuid4())

    assert [item.vacancy.title for item in result] == ["Strongest", "Recent tie", "Older tie"]
