"""CLI entry point for initializing the baseline Skill ontology."""

from sqlalchemy import func, select

from app.db.session import SessionLocal
from app.models.skill import Skill
from app.models.skill_alias import SkillAlias
from app.services.skill_ontology_seed import seed_skill_ontology


def main() -> None:
    with SessionLocal.begin() as session:
        result = seed_skill_ontology(session)
        total_skills = session.scalar(select(func.count()).select_from(Skill)) or 0
        total_aliases = session.scalar(select(func.count()).select_from(SkillAlias)) or 0
    print(
        "Skill ontology seed completed: "
        f"skills_created={result.skills_created} skills_reused={result.skills_reused} "
        f"aliases_created={result.aliases_created} aliases_reused={result.aliases_reused} "
        f"total_skills={total_skills} total_aliases={total_aliases}"
    )


if __name__ == "__main__":
    main()
