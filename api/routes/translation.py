from fastapi import APIRouter
from api.models import TranslateRequest, TargetRequest
from core.multilanguage import MultiLanguage

router = APIRouter(prefix="/translate", tags=["Translation"])

@router.post("/to-traditional-chinese")
async def translate_to_traditional_chinese_api(request: TranslateRequest):
    """將文字翻譯為繁體中文"""
    translated, lang = MultiLanguage.translate_to_traditional_chinese(request.text)
    return {"translated_text": translated, "source_language": lang}

@router.post("/to-target-language")
async def translate_to_target_language_api(request: TargetRequest):
    """將文字翻譯為指定語言"""
    translated = MultiLanguage.translate_to_target_language(request.text, request.target_language)
    return {"translated_text": translated, "dest_language": request.target_language}
