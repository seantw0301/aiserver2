from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from core.sch import ScheduleManager
from core.common import room_status_manager
from utils import run_in_executor, validate_date_format

router = APIRouter(prefix="/schedule", tags=["Schedule"])

# 創建管理器實例
schedule_manager = ScheduleManager()

@router.get("/staff/{name}/{target_date}", summary="獲取指定師傅指定日期的班表")
async def get_schedule_by_name(name: str, target_date: str):
    """獲取指定師傅指定日期的班表 (5分鐘間隔)"""
    if not validate_date_format(target_date):
        raise HTTPException(status_code=400, detail='日期格式錯誤，請使用 YYYY-MM-DD 格式')
    
    try:
        schedule = await run_in_executor(schedule_manager.get_schedule_by_name, name, target_date)
        if schedule:
            return {
                'success': True,
                'data': schedule
            }
        else:
            raise HTTPException(status_code=404, detail='找不到指定師傅或班表資料')
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/date/{target_date}", summary="獲取指定日期所有師傅的班表")
async def get_schedule_by_date(target_date: str):
    """獲取指定日期所有師傅的班表 (5分鐘間隔)"""
    if not validate_date_format(target_date):
        raise HTTPException(status_code=400, detail='日期格式錯誤，請使用 YYYY-MM-DD 格式')
    
    try:
        schedules = await run_in_executor(schedule_manager.get_schedule_by_date, target_date)
        return {
            'success': True,
            'data': schedules
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/staff/{name}/{target_date}/labels", summary="獲取帶時間標籤的班表")
async def get_schedule_with_labels(name: str, target_date: str):
    """獲取帶時間標籤的班表 (用於除錯和展示)"""
    if not validate_date_format(target_date):
        raise HTTPException(status_code=400, detail='日期格式錯誤，請使用 YYYY-MM-DD 格式')
    
    try:
        schedule = await run_in_executor(schedule_manager.get_schedule_with_time_labels, name, target_date)
        if schedule:
            return {
                'success': True,
                'data': schedule
            }
        else:
            raise HTTPException(status_code=404, detail='找不到指定師傅或班表資料')
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/staff/{name}/{target_date}/pretty", summary="獲取以易讀格式顯示的班表")
async def get_schedule_pretty_display(name: str, target_date: str, include_tasks: bool = Query(True, description="是否包含工作時段")):
    """獲取以易讀格式顯示的班表"""
    if not validate_date_format(target_date):
        raise HTTPException(status_code=400, detail='日期格式錯誤，請使用 YYYY-MM-DD 格式')
    
    try:
        pretty_display = await run_in_executor(schedule_manager.get_schedule_pretty_display, name, target_date, include_tasks)
        return {
            'success': True,
            'display': pretty_display
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/staff-shifts/date/{target_date}", summary="獲取指定日期所有師傅的排班時間")
async def get_staff_shifts_by_date(target_date: str, store: Optional[str] = Query(None, description="店家名稱")):
    """
    獲取指定日期所有師傅的排班時間
    
    Args:
        target_date: 日期，格式為 YYYY-MM-DD 或 YYYY/MM/DD
        store: 店家名稱，可選
    
    Returns:
        JSON 格式的師傅排班時間
    """
    try:
        result = await run_in_executor(room_status_manager.get_staff_shifts_by_date, target_date, store)
        return {
            'success': True,
            'data': result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'獲取師傅排班資料錯誤: {str(e)}')
