from pydantic import BaseModel, Field
from typing import Optional, List

# Translation Models
class TranslateRequest(BaseModel):
    text: str

class TargetRequest(BaseModel):
    text: str
    target_language: str

# Language Models
class LineUserLanguageRequest(BaseModel):
    line_user_id: str

class LineUserSetLanguageRequest(BaseModel):
    line_user_id: str
    language: str

# Store Models
class StoreCreate(BaseModel):
    name: str = Field(..., description="店家名稱")
    address: Optional[str] = Field(None, description="店家地址")
    phone: Optional[str] = Field(None, description="聯絡電話")
    description: Optional[str] = Field(None, description="店家描述")

class StoreUpdate(BaseModel):
    name: Optional[str] = Field(None, description="店家名稱")
    address: Optional[str] = Field(None, description="店家地址")
    phone: Optional[str] = Field(None, description="聯絡電話")
    description: Optional[str] = Field(None, description="店家描述")

# Task Models
class TaskCreate(BaseModel):
    customer_name: str = Field(..., description="客戶名稱")
    start: str = Field(..., description="開始時間 (ISO格式)")
    end: str = Field(..., description="結束時間 (ISO格式)")
    staff_name: Optional[str] = Field(None, description="師傅名稱")
    store_id: Optional[int] = Field(None, description="店家ID")
    room_id: Optional[int] = Field(None, description="房間ID")
    service_type: Optional[str] = Field(None, description="服務類型")
    price: Optional[float] = Field(None, description="價格")
    notes: Optional[str] = Field(None, description="備註")

class TaskUpdate(BaseModel):
    customer_name: Optional[str] = Field(None, description="客戶名稱")
    start: Optional[str] = Field(None, description="開始時間 (ISO格式)")
    end: Optional[str] = Field(None, description="結束時間 (ISO格式)")
    staff_name: Optional[str] = Field(None, description="師傅名稱")
    store_id: Optional[int] = Field(None, description="店家ID")
    room_id: Optional[int] = Field(None, description="房間ID")
    service_type: Optional[str] = Field(None, description="服務類型")
    price: Optional[float] = Field(None, description="價格")
    notes: Optional[str] = Field(None, description="備註")
    is_confirmed: Optional[bool] = Field(None, description="是否確認")

class TaskConfirm(BaseModel):
    is_confirmed: bool = Field(True, description="是否確認")

# Appointment Models
class AppointmentQuery(BaseModel):
    branch: str = Field(..., description="分店名稱")
    date: str = Field(..., description="日期")
    time: str = Field(..., description="時間")
    project: int = Field(..., description="項目時長（分鐘）")
    count: int = Field(..., description="人數")
    masseur: Optional[List[str]] = Field(None, description="指定師傅列表")

class PreferStoreQuery(BaseModel):
    date: str = Field(..., description="日期 (YYYY/MM/DD 或 YYYY-MM-DD)")
    masseur_name: str = Field(..., description="師傅中文名")

# Room Models
class RoomAvailabilityQuery(BaseModel):
    store_id: int = Field(..., description="店家ID")
    date: str = Field(..., description="日期")
    start_time: str = Field(..., description="開始時間")
    duration_minutes: int = Field(..., description="持續時間（分鐘）")
    required_rooms: int = Field(1, description="需要的房間數量")

# Natural Language Models
class NaturalLanguageRequest(BaseModel):
    key: str = Field(..., description="用戶的唯一識別鍵")
    message: str = Field(..., description="客戶輸入的自然語言文字")
