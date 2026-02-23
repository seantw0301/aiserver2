from fastapi import APIRouter, HTTPException
from api.models import StoreCreate, StoreUpdate
from core.store import StoreManager
from utils import run_in_executor

router = APIRouter(prefix="/stores", tags=["Stores"])

# 創建管理器實例
store_manager = StoreManager()

@router.get("", summary="獲取所有店家列表")
async def get_all_stores():
    """獲取所有店家列表"""
    try:
        stores = await run_in_executor(store_manager.get_all_stores)
        return {
            'success': True,
            'data': stores,
            'count': len(stores)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/summary", summary="獲取店家摘要資訊")
async def get_stores_summary():
    """獲取店家摘要資訊"""
    try:
        summary = await run_in_executor(store_manager.get_store_summary)
        return {
            'success': True,
            'data': summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search/{keyword}", summary="搜索店家")
async def search_stores(keyword: str):
    """搜索店家"""
    try:
        stores = await run_in_executor(store_manager.search_stores, keyword)
        return {
            'success': True,
            'data': stores,
            'count': len(stores),
            'keyword': keyword
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{store_id}", summary="根據ID獲取店家資訊")
async def get_store_by_id(store_id: int):
    """根據ID獲取店家資訊"""
    try:
        store = await run_in_executor(store_manager.get_store_by_id, store_id)
        if store:
            return {
                'success': True,
                'data': store
            }
        else:
            raise HTTPException(status_code=404, detail='找不到指定店家')
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/name/{name}", summary="根據名稱獲取店家資訊")
async def get_store_by_name(name: str):
    """根據名稱獲取店家資訊"""
    try:
        store = await run_in_executor(store_manager.get_store_by_name, name)
        if store:
            return {
                'success': True,
                'data': store
            }
        else:
            raise HTTPException(status_code=404, detail='找不到指定店家')
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@router.post("", summary="創建新店家", status_code=201)
async def create_store(store_data: StoreCreate):
    """創建新店家"""
    try:
        store_dict = store_data.dict()
        store_id = await run_in_executor(store_manager.create_store, store_dict)
        if store_id:
            return {
                'success': True,
                'data': {'id': store_id},
                'message': '店家創建成功'
            }
        else:
            raise HTTPException(status_code=500, detail='創建店家失敗')
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{store_id}", summary="更新店家資訊")
async def update_store(store_id: int, store_data: StoreUpdate):
    """更新店家資訊"""
    try:
        store_dict = store_data.dict(exclude_unset=True)
        success = await run_in_executor(store_manager.update_store, store_id, store_dict)
        if success:
            return {
                'success': True,
                'message': '店家更新成功'
            }
        else:
            raise HTTPException(status_code=404, detail='更新店家失敗或店家不存在')
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{store_id}", summary="刪除店家")
async def delete_store(store_id: int):
    """刪除店家"""
    try:
        success = await run_in_executor(store_manager.delete_store, store_id)
        if success:
            return {
                'success': True,
                'message': '店家刪除成功'
            }
        else:
            raise HTTPException(status_code=404, detail='刪除店家失敗或店家不存在')
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))
