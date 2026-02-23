import sys

import uvicorn

from .settings import get_settings


def run_api_server() -> None:
    settings = get_settings()

    print("=" * 60)
    print("🚀 啟動師傅班表管理 API 服務器")
    print("=" * 60)
    print(f"📍 服務地址: http://{settings.api_host}:{settings.api_port}")
    print(f"📚 API 文檔: http://{settings.api_host}:{settings.api_port}/docs")
    print(f"📖 ReDoc 文檔: http://{settings.api_host}:{settings.api_port}/redoc")
    print(f"🐛 調試模式: {'開啟' if settings.debug else '關閉'}")
    print(f"👥 工作進程: {settings.workers}")
    print("=" * 60)

    try:
        uvicorn.run(
            "api.bootstrap.application:app",
            host=settings.api_host,
            port=settings.api_port,
            reload=settings.debug,
            workers=settings.workers,
            access_log=True,
            log_level="debug" if settings.debug else "info",
            loop="asyncio",
        )
    except KeyboardInterrupt:
        print("\n⏹️  收到中斷信號，正在關閉服務器...")
    except Exception as exc:
        print(f"❌ 啟動服務器時發生錯誤: {exc}")
        sys.exit(1)
    finally:
        print("👋 服務器已關閉")
