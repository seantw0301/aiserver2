-- 將 skip_keywords 資料表轉換為 MyISAM 引擎
-- MyISAM 引擎支援 information_schema.tables.UPDATE_TIME 欄位

-- 1. 檢查目前的引擎類型
SELECT TABLE_NAME, ENGINE, UPDATE_TIME, CREATE_TIME 
FROM information_schema.tables 
WHERE TABLE_SCHEMA = DATABASE() 
  AND TABLE_NAME = 'skip_keywords';

-- 2. 轉換為 MyISAM 引擎
ALTER TABLE skip_keywords ENGINE = MyISAM;

-- 3. 驗證轉換結果
SELECT TABLE_NAME, ENGINE, UPDATE_TIME, CREATE_TIME 
FROM information_schema.tables 
WHERE TABLE_SCHEMA = DATABASE() 
  AND TABLE_NAME = 'skip_keywords';

-- 注意事項：
-- - MyISAM 不支援交易（Transactions）
-- - MyISAM 不支援外鍵約束（Foreign Keys）
-- - MyISAM 使用表級鎖定，並發性能較 InnoDB 差
-- - 但 MyISAM 會自動維護 UPDATE_TIME 欄位
