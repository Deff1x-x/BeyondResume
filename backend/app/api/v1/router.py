from fastapi import APIRouter

from app.api.v1 import (
    auth,
    candidate,
    career_companion,
    dashboard,
    employer,
    evidence,
    github,
    health,
    jobs,
    resume,
    roadmap,
    skill_passport,
    users,
)

router = APIRouter(prefix="/api/v1")
router.include_router(health.router)
router.include_router(auth.router)
router.include_router(candidate.router)
router.include_router(career_companion.router)
router.include_router(dashboard.router)
router.include_router(evidence.router)
router.include_router(resume.router)
router.include_router(github.router)
router.include_router(skill_passport.router)
router.include_router(roadmap.router)
router.include_router(employer.router)
router.include_router(jobs.router)
router.include_router(users.router)
