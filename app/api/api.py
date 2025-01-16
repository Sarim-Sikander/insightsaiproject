from fastapi import APIRouter

from app.api.endpoints import documents, elasticsearch, home, llm

router = APIRouter()

router.include_router(home.router, tags=["home"])
router.include_router(documents.router, tags=["documents"])
router.include_router(elasticsearch.router, tags=["es"])
router.include_router(llm.router, tags=["llm"])
