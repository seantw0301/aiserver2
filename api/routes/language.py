from fastapi import APIRouter
from api.models import LineUserLanguageRequest, LineUserSetLanguageRequest
from modules import lang

router = APIRouter(prefix="/line-user", tags=["Language"])

@router.post("/language", summary="查詢 LINE user 語言")
async def get_line_user_language(data: LineUserLanguageRequest):
    """查詢 LINE 使用者的語言設定"""
    user_lang = lang.get_user_language(data.line_user_id)
    return {"success": True, "language": user_lang if user_lang else ""}

@router.post("/set-language", summary="設置 LINE user 語言")
async def set_line_user_language(data: LineUserSetLanguageRequest):
    """設置 LINE 使用者的語言"""
    ok = lang.set_user_language(data.line_user_id, data.language)
    return {"success": ok}
