from app.services.career_companion.context import resolve_skill_id


def test_resolve_skill_id_uses_canonical_name(monkeypatch):
    class FakeSkill:
        id = "skill-1"
        canonical_name = "Docker"
        normalized_name = "docker"

    class FakeResult:
        def scalars(self):
            return self

        def all(self):
            return [FakeSkill()]

    class FakeSession:
        def execute(self, _stmt):
            return FakeResult()

    assert resolve_skill_id(FakeSession(), "Docker") == "skill-1"
    assert resolve_skill_id(FakeSession(), "docker") == "skill-1"
    assert resolve_skill_id(FakeSession(), "Telepathy") is None
