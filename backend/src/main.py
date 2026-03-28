from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from src.agent.router import router as agent_router
from src.auth.router import router as auth_router
from src.config import settings
from src.database import Base, engine
from src.dashboard.router import router as dashboard_router
from src.exceptions import BusinessException
from src.schemas import BaseResponse
from src.task.router import router as task_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)
web_dir = Path(__file__).resolve().parents[1] / "web"


@app.exception_handler(BusinessException)
async def business_exception_handler(_: Request, exc: BusinessException) -> JSONResponse:
    return JSONResponse(status_code=200, content=BaseResponse(code=exc.code, message=exc.message, data=None).model_dump())


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content=BaseResponse(code=exc.status_code, message=str(exc.detail), data=None).model_dump())


@app.get("/")
async def dashboard_page() -> FileResponse:
    return FileResponse(web_dir / "index.html")


@app.get("/dashboard")
async def dashboard_alias_page() -> FileResponse:
    return FileResponse(web_dir / "index.html")


app.mount("/web", StaticFiles(directory=web_dir), name="web")
app.include_router(auth_router, prefix="/api")
app.include_router(agent_router, prefix="/api")
app.include_router(task_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
