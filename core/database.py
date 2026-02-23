import mysql.connector
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

class DatabaseConfig:
    def __init__(self):
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = int(os.getenv('DB_PORT', 3306))
        self.user = os.getenv('DB_USER', 'root')
        self.password = os.getenv('DB_PASSWORD', '')
        self.database = os.getenv('DB_NAME', 'senspa_sch')

    def get_connection(self):
        """建立資料庫連線"""
        try:
            connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                charset='utf8'
            )
            return connection
        except mysql.connector.Error as err:
            print(f"資料庫連線錯誤: {err}")
            return None

# 全域資料庫配置實例
db_config = DatabaseConfig()
