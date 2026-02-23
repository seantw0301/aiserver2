from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from api.models import TaskCreate, TaskUpdate, TaskConfirm
from core.tasks import TaskManager
from utils import run_in_executor, validate_datetime_format, validate_date_format

router = APIRouter(prefix="/tasks", tags=["Tasks"])

# 創建管理器實例
task_manager = TaskManager()

@router.get("", summary="獲取所有預約列表")
async def get_all_tasks(limit: int = Query(100, ge=1, le=1000), offset: int = Query(0, ge=0)):
    """獲取所有預約列表（支援分頁）"""
    try:
        tasks = await run_in_executor(task_manager.get_all_tasks, limit, offset)
        return {
            'success': True,
            'data': tasks,
            'count': len(tasks),
            'limit': limit,
            'offset': offset
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.get("/{task_id}", summary="根據ID獲取預約資訊")
async def get_task_by_id(task_id: int):
    """根據ID獲取預約資訊"""
    try:
        task = await run_in_executor(task_manager.get_task_by_id, task_id)
        if task:
            return {
                'success': True,
                'data': task
            }
        else:
            raise HTTPException(status_code=404, detail='找不到指定預約')
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/customer/{customer_name}", summary="根據客戶名稱獲取預約記錄")
async def get_tasks_by_customer(customer_name: str):
    """根據客戶名稱獲取預約記錄"""
    try:
        tasks = await run_in_executor(task_manager.get_tasks_by_customer, customer_name)
        return {
            'success': True,
            'data': tasks,
            'count': len(tasks),
            'customer_name': customer_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("", summary="創建新預約", status_code=201)
async def create_task(task_data: TaskCreate):
    """創建新預約"""
    if not validate_datetime_format(task_data.start):
        raise HTTPException(status_code=400, detail='start 日期時間格式錯誤，請使用 ISO 格式')
    
    if not validate_datetime_format(task_data.end):
        raise HTTPException(status_code=400, detail='end 日期時間格式錯誤，請使用 ISO 格式')
    
    try:
        task_dict = task_data.dict()
        task_id = await run_in_executor(task_manager.create_task, task_dict)
        if task_id:
            return {
                'success': True,
                'data': {'id': task_id},
                'message': '預約創建成功'
            }
        else:
            raise HTTPException(status_code=500, detail='創建預約失敗')
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{task_id}", summary="更新預約資訊")
async def update_task(task_id: int, task_data: TaskUpdate):
    """更新預約資訊"""
    task_dict = task_data.dict(exclude_unset=True)
    
    for field in ['start', 'end']:
        if field in task_dict:
            if not validate_datetime_format(task_dict[field]):
                raise HTTPException(status_code=400, detail=f'{field} 日期時間格式錯誤，請使用 ISO 格式')
    
    try:
        success = await run_in_executor(task_manager.update_task, task_id, task_dict)
        if success:
            return {
                'success': True,
                'message': '預約更新成功'
            }
        else:
            raise HTTPException(status_code=404, detail='更新預約失敗或預約不存在')
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{task_id}", summary="刪除預約")
async def delete_task(task_id: int):
    """刪除預約"""
    try:
        success = await run_in_executor(task_manager.delete_task, task_id)
        if success:
            return {
                'success': True,
                'message': '預約刪除成功'
            }
        else:
            raise HTTPException(status_code=404, detail='刪除預約失敗或預約不存在')
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{task_id}/confirm", summary="師傅確認預約")
async def confirm_task(task_id: int, confirm_data: TaskConfirm):
    """師傅確認預約"""
    try:
        success = await run_in_executor(task_manager.confirm_task, task_id, confirm_data.is_confirmed)
        if success:
            action = '確認' if confirm_data.is_confirmed else '取消確認'
            return {
                'success': True,
                'message': f'預約{action}成功'
            }
        else:
            raise HTTPException(status_code=404, detail='確認預約失敗或預約不存在')
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search/{keyword}", summary="搜索預約")
async def search_tasks(keyword: str):
    """搜索預約"""
    try:
        tasks = await run_in_executor(task_manager.search_tasks, keyword)
        return {
            'success': True,
            'data': tasks,
            'count': len(tasks),
            'keyword': keyword
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statistics", summary="獲取預約統計資訊")
async def get_task_statistics(
    start_date: Optional[str] = Query(default=None, description="開始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(default=None, description="結束日期 (YYYY-MM-DD)")
):
    """獲取預約統計資訊"""
    if start_date and not validate_date_format(start_date):
        raise HTTPException(status_code=400, detail='start_date 日期格式錯誤，請使用 YYYY-MM-DD 格式')
    
    if end_date and not validate_date_format(end_date):
        raise HTTPException(status_code=400, detail='end_date 日期格式錯誤，請使用 YYYY-MM-DD 格式')
    
    try:
        statistics = await run_in_executor(task_manager.get_task_statistics, start_date, end_date)
        return {
            'success': True,
            'data': statistics
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
