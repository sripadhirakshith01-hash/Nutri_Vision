from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from mysql.connector import Error as MySQLError

from app.api import auth, chatbot, dashboard, food, foods, meals, nutrition, predict, predictions, profile
from app.config import PROJECT_ROOT, get_settings
from app.database.init_db import migrate
from app.ml.model_service import load_model_bundle


@asynccontextmanager
async def lifespan(_app: FastAPI):
    migrate()
    load_model_bundle()
    yield


settings = get_settings()
FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"
INDEX_HTML = FRONTEND_DIST / "index.html"

app = FastAPI(
    title="NutriVision AI",
    description="See your food. Understand your nutrition. Food-101 recognition, meal logging, and NutriCoach.",
    version="2.0.0",
    lifespan=lifespan,
)

cors_origins = settings.cors_origin_list
if cors_origins == ["*"]:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(predict.router)
app.include_router(food.router)
app.include_router(predictions.router)
app.include_router(meals.router)
app.include_router(dashboard.router)
app.include_router(nutrition.router)
app.include_router(foods.router)
app.include_router(chatbot.router)

uploads = settings.resolved_upload_dir
uploads.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads)), name="uploads")


@app.get("/api/health")
def health():
    from app.database.connection import ping_database

    db_ok = False
    try:
        db_ok = ping_database()
    except MySQLError:
        db_ok = False
    return {"status": "ok" if db_ok else "degraded", "database": db_ok}


if settings.serve_frontend and INDEX_HTML.exists():
    assets = FRONTEND_DIST / "assets"
    if assets.exists():
        app.mount("/assets", StaticFiles(directory=str(assets)), name="assets")

    @app.get("/")
    def root():
        return FileResponse(INDEX_HTML)

    @app.get("/{full_path:path}")
    def spa(full_path: str):
        if full_path.startswith("api/") or full_path.startswith("uploads/"):
            raise HTTPException(status_code=404, detail="Not found")
        candidate = FRONTEND_DIST / full_path
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(INDEX_HTML)
else:

    @app.get("/")
    def root():
        return RedirectResponse("http://localhost:5173")


@app.exception_handler(RequestValidationError)
async def validation_handler(_request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"detail": "Invalid request data.", "errors": exc.errors()})


@app.exception_handler(MySQLError)
async def mysql_handler(_request: Request, _exc: MySQLError):
    return JSONResponse(status_code=503, content={"detail": "Database connection failed. Please try again later."})
