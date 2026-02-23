from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routes import (
    language_router,
    parse_router,
    rooms_router,
    schedule_router,
    staffs_router,
    stores_router,
    tasks_router,
    translation_router,
)

load_dotenv()


def create_app() -> FastAPI:
    app = FastAPI(
        title="師傅班表管理API",
        description="支援非同步處理的師傅班表管理系統 API",
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(translation_router)
    app.include_router(language_router)
    app.include_router(parse_router)
    app.include_router(staffs_router)
    app.include_router(stores_router)
    app.include_router(tasks_router)
    app.include_router(schedule_router)
    app.include_router(rooms_router)

    @app.get("/", summary="API首頁")
    async def root() -> dict:
        return {
            "name": "師傅班表管理API",
            "version": "2.0.0",
            "status": "running",
            "features": [
                "支援非同步處理",
                "支援多個併發連接",
                "自動生成 API 文檔",
                "數據驗證和類型檢查",
            ],
            "documentation": {
                "swagger_ui": "/docs",
                "redoc": "/redoc",
            },
        }

    @app.exception_handler(500)
    async def internal_server_error(_: Request, __: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "內部服務器錯誤",
            },
        )

    @app.exception_handler(404)
    async def not_found_error(_: Request, __: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "error": "找不到請求的資源",
            },
        )

    return app


app = create_app()
