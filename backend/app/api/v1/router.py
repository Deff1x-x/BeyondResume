from fastapi import APIRouter

from app.api.v1 import auth, candidate, github, jobs, resume, roadmap, skill_passport, users

router = APIRouter(prefix="/api/v1")
router.include_router(auth.router)
router.include_router(candidate.router)
router.include_router(resume.router)
router.include_router(github.router)
router.include_router(skill_passport.router)
router.include_router(roadmap.router)
router.include_router(jobs.router)
router.include_router(users.router)
