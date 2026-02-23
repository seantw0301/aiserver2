from fastapi import APIRouter, HTTPException
from core.staffs import StaffManager
from utils import run_in_executor

router = APIRouter(prefix="/staffs", tags=["Staffs"])

# 創建管理器實例
staff_manager = StaffManager()

@router.get("", summary="獲取所有師傅列表")
async def get_all_staffs():
    """獲取所有師傅列表"""
    try:
        staffs = await run_in_executor(staff_manager.get_all_staffs)
        return {
            'success': True,
            'data': staffs,
            'count': len(staffs)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{staff_id}", summary="根據ID獲取師傅資訊")
async def get_staff_by_id(staff_id: int):
    """根據ID獲取師傅資訊"""
    try:
        staff = await run_in_executor(staff_manager.get_staff_by_id, staff_id)
        if staff:
            return {
                'success': True,
                'data': staff
            }
        else:
            raise HTTPException(status_code=404, detail='找不到指定師傅')
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/name/{name}", summary="根據姓名獲取師傅資訊")
async def get_staff_by_name(name: str):
    """根據姓名獲取師傅資訊"""
    try:
        staff = await run_in_executor(staff_manager.get_staff_by_name, name)
        if staff:
            return {
                'success': True,
                'data': staff
            }
        else:
            raise HTTPException(status_code=404, detail='找不到指定師傅')
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))
