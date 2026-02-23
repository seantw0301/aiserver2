import asyncio

async def run_in_executor(func, *args):
    """在執行器中運行同步函數"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, func, *args)
