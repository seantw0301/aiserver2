from pydantic import BaseModel, Field
from typing import Optional, List

class NaturalLanguageResponse(BaseModel):
    branch: str = Field(..., description="店家名稱")
    masseur: List[str] = Field(..., description="師傅名稱列表")
    date: str = Field(..., description="預約日期 (YYYY/MM/DD)")
    time: str = Field(..., description="開始時間 (HH:MM)")
    project: int = Field(..., description="項目時間 (60/90/120分鐘)")
    count: int = Field(..., description="客人數量")
    isReservation: Optional[bool] = Field(None, description="是否為預約相關")
    is_keyword_match: Optional[bool] = Field(None, description="是否匹配關鍵字")
    response_message: Optional[str] = Field(None, description="關鍵字匹配的回應消息")
    success: Optional[bool] = Field(None, description="操作是否成功")
    message: Optional[str] = Field(None, description="操作消息")
    error: Optional[str] = Field(None, description="錯誤消息")
