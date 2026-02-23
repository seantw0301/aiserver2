# 處理中文時間字串 X點X分  X點半 X時
import re
from handle_time2025_util import chinese_to_arabic

def format_time_string_1(time_str, time_format_type=3):
	"""
	將中文時間字串轉為標準時間格式
	time_format_type=3: 11:30, 12:50:00, 12.5 -> 11:30:00, 12:50:00, 12:30:00
	time_format_type=2: 11:30, 12:50:00, 12.5 -> 11:30, 12:50, 12:30
	"""
	s = chinese_to_arabic(time_str)
	
	# 檢查是否只有時間段詞
	if s.strip() == '早上' or s.strip() == '上午':
		if time_format_type == 3:
			return "09:00:00"
		else:
			return "09:00"
	elif s.strip() == '中午':
		if time_format_type == 3:
			return "12:00:00"
		else:
			return "12:00"
	elif s.strip() == '下午':
		if time_format_type == 3:
			return "13:00:00"
		else:
			return "13:00"
	elif s.strip() == '傍晚':
		if time_format_type == 3:
			return "17:00:00"
		else:
			return "17:00"
	elif s.strip() == '晚上':
		if time_format_type == 3:
			return "18:00:00"
		else:
			return "18:00"
	elif s.strip() == '凌晨':
		if time_format_type == 3:
			return "01:00:00"
		else:
			return "01:00"
	elif s.strip() == '清晨':
		if time_format_type == 3:
			return "06:00:00"
		else:
			return "06:00"
	elif s.strip() == '深夜':
		if time_format_type == 3:
			return "22:00:00"
		else:
			return "22:00"
	elif s.strip() == '午夜':
		if time_format_type == 3:
			return "24:00:00"
		else:
			return "24:00"
	
	# 處理上午/下午時間轉換
	hour_offset = 0
	if '下午' in s or '晚上' in s or '傍晚' in s or '深夜' in s:
		hour_offset = 12
	elif '上午' in s or '早上' in s or '清晨' in s or '凌晨' in s or '午夜' in s or '中午' in s:
		hour_offset = 0
	else:
		# 對於沒有明確標記的時間，假設為下午時間（中午12點後）
		hour_offset = 12
	
	# 移除時間前綴
	s = re.sub(r'(上午|下午|中午|晚上|早上|凌晨|清晨|傍晚|深夜|午夜)', '', s)
	
	s = s.replace('點半', ':30').replace('點', ':').replace('時', ':').replace('分', '').replace('：', ':')
	s = re.sub(r':+', ':', s)
	s = s.strip(':')
	
	# 將 12.5 轉為 12:30
	match = re.match(r'^(\d{1,2})[\.|．](5|30)$', s)
	if match:
		hour = int(match.group(1)) + hour_offset
		minute = 30
		s = f"{hour}:{minute:02d}"
	# 若只有小時
	elif re.match(r'^\d{1,2}$', s):
		hour = int(s) + hour_offset
		s = f"{hour}:00"
	# 若只有小時:分鐘
	elif re.match(r'^\d{1,2}:\d{1,2}$', s):
		hour, minute = map(int, s.split(':'))
		hour += hour_offset
		s = f"{hour}:{minute:02d}"
	# 若已經有秒
	elif re.match(r'^\d{1,2}:\d{1,2}:\d{1,2}$', s):
		hour, minute, second = map(int, s.split(':'))
		hour += hour_offset
		s = f"{hour}:{minute:02d}:{second:02d}"
	# 若有小時:分鐘:但分鐘為一位數
	elif re.match(r'^\d{1,2}:\d$', s):
		hour, minute = s.split(':')
		hour = int(hour) + hour_offset
		s = f"{hour}:{int(minute):02d}"
	# 其他情況不處理

	if time_format_type == 3:
		# 轉為 HH:MM:00
		if re.match(r'^\d{1,2}:\d{2}$', s):
			s = s + ':00'
		elif re.match(r'^\d{1,2}:\d{2}:\d{2}$', s):
			pass
	elif time_format_type == 2:
		# 只保留 HH:MM
		if re.match(r'^\d{1,2}:\d{2}:\d{2}$', s):
			s = ':'.join(s.split(':')[:2])
	return s
