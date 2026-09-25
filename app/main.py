from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.api.auth import router as auth_router
from app.api.projects import router as projects_router
from app.api.tasks import router as tasks_router
from app.api.time_entries import router as time_entries_router
from app.database import engine


app = FastAPI(
    title="ITоднушка Worklog",
    description="Учёт рабочего времени и рентабельности проектов",
    version="0.1.0",
)

app.include_router(projects_router)
app.include_router(auth_router)
app.include_router(tasks_router)
app.include_router(time_entries_router)

app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static",
)


@app.get("/", include_in_schema=False)
async def frontend():
    return FileResponse("app/static/index.html")


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/health/db")
async def database_health_check():
    async with engine.connect() as connection:
        result = await connection.execute(text("SELECT 1"))

    return {
        "status": "ok",
        "database": result.scalar(),
    }