import redis
import json
from common import RoomStatusManager
from sch import ScheduleManager

class MatrixManager:

    REDIS_HOST = 'localhost'
    REDIS_PORT = 6379
    REDIS_DB = 0
    REDIS_EXPIRE = 12 * 60 * 60  # 12小時

    STORE_MAP = {
        1: '西門',
        2: '延吉',
        # ...可擴充更多店
    }

    ROOM_COUNT = {
        '西門': 4,  # 假設西門有4間房
        '延吉': 4, # 假設延吉有4間房
        # ...可擴充更多店
    }

    def __init__(self):
        self.r = redis.Redis(host=self.REDIS_HOST, port=self.REDIS_PORT, db=self.REDIS_DB)
        self.schedule_manager = ScheduleManager()
        self.roomStatus_manager = RoomStatusManager()


    def update(self, date_str):
        """
        立即更新指定日期的所有師傅矩陣，並存放至redis
        """
        self.r = redis.Redis(host=self.REDIS_HOST, port=self.REDIS_PORT, db=self.REDIS_DB)
        room_occupancy = {}
        #取得各間店的房間佔用情況
        for store_id, store_name in self.STORE_MAP.items():
            room_occupancy[store_name] = self.roomStatus_manager._get_room_occupancy_from_tasks(store_id, date_str)
        #取得當日有排班的師傅
        staff_names = self.schedule_manager.get_scheduled_staff_names(date_str)
        for staff_name in staff_names:
            #取出指定師傅的詳細排班 
            schedule = self.schedule_manager.get_schedule_by_name(staff_name, date_str, include_tasks=True)
            for store_name in self.STORE_MAP.values():
                for room_num in range(1, self.ROOM_COUNT[store_name]+1):
                    room_blocks = room_occupancy[store_name].get(room_num, [0]*288)
                    available_blocks = [int(s and not r) for s, r in zip(schedule['schedule'], room_blocks)]
                    redis_key = f"{date_str}-{store_name}-{room_num}-{staff_name}"
                    self.r.set(redis_key, json.dumps(available_blocks), ex=self.REDIS_EXPIRE)
                    print(f"Updated Redis key: {redis_key}")

    def update_by_name(self, date_str, staff_name):
        """
        立即更新某師傅在指定日期的矩陣資料，並存放至redis
        """
        staff_names = self.schedule_manager.get_scheduled_staff_names(date_str)
        if staff_name not in staff_names:
            return
        self.r = redis.Redis(host=self.REDIS_HOST, port=self.REDIS_PORT, db=self.REDIS_DB)
        room_occupancy = {}
        #取得各間店的房間佔用情況
        for store_id, store_name in self.STORE_MAP.items():
            room_occupancy[store_name] = self.roomStatus_manager._get_room_occupancy_from_tasks(store_id, date_str)

        schedule = self.schedule_manager.get_schedule_by_name(staff_name, date_str, include_tasks=True)
        for store_name in self.STORE_MAP.values():
            for room_num in range(1, self.ROOM_COUNT[store_name]+1):
                room_blocks = room_occupancy[store_name].get(room_num, [0]*288)
                available_blocks = [int(s and not r) for s, r in zip(schedule['schedule'], room_blocks)]
                redis_key = f"{date_str}-{store_name}-{room_num}-{staff_name}"
                self.r.set(redis_key, json.dumps(available_blocks), ex=self.REDIS_EXPIRE)
                print(f"Updated Redis key: {redis_key}")
