import os
import datetime
import requests
import chinese_calendar as calendar
from supabase import create_client, Client

def fetch_dorm_config(supabase: Client, dorm_id: str) -> dict:
    try:
        response = supabase.table("dorm_rules").select("*").eq("dorm_id", dorm_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"[Error] 数据库查询失败: {e}")
        return None

def execute_pushplus_notice(token: str, topic: str, title: str, content: str):
    url = "http://www.pushplus.plus/send"
    payload = {"token": token, "title": title, "content": content, "template": "markdown", "topic": topic}
    try:
        res = requests.post(url, json=payload)
        res.raise_for_status()
        print(f"[Success] PushPlus 推送成功: {res.json()}")
    except Exception as e:
        print(f"[Error] PushPlus 推送失败: {e}")

def main():
    sb_url = os.environ.get("SUPABASE_URL")
    sb_key = os.environ.get("SUPABASE_KEY")
    push_token = os.environ.get("PUSHPLUS_TOKEN")

    if not all([sb_url, sb_key, push_token]):
        print("[Fatal] 环境变量缺失。")
        return

    # --- [3.1.2 时区修复 & 精准识别] 强制使用北京时间，且只在法定大长假休眠 ---
    # 获取全球统一 UTC 时间，手动加上 8 小时转换为北京时间
    utc_now = datetime.datetime.now(datetime.timezone.utc)
    beijing_now = utc_now + datetime.timedelta(hours=8)
    today = beijing_now.date() 
    
    on_holiday, holiday_name = calendar.get_holiday_detail(today)
    
    # 只有当今天是休息日且有明确节日名称时，才判定为“放假回家的日子”
    if on_holiday and holiday_name is not None:
        print(f"[Info] 北京时间 {today} 是 {holiday_name}，系统休眠。")
        return
    # ----------------------------------------

    supabase: Client = create_client(sb_url, sb_key)
    dorm_id = "212"

    data = fetch_dorm_config(supabase, dorm_id)
    if not data:
        print(f"[Warning] 未获取到配置。")
        return

    roommates = [name.strip() for name in data["roommates"].split(",")]
    anchor_date = datetime.datetime.strptime(data["anchor_date"], "%Y-%m-%d").date()
    anchor_person = data["anchor_person"]
    push_topic = data["pushplus_topic"]

    if anchor_person not in roommates:
        print(f"[Fatal] 初始人不在名单中。")
        return

    # 这里的 today 已经统一切换成了准确的北京时间
    days_passed = (today - anchor_date).days
    num_people = len(roommates)
    anchor_index = roommates.index(anchor_person)
    today_index = (days_passed + anchor_index) % num_people
    tomorrow_index = (days_passed + 1 + anchor_index) % num_people

    today_person = roommates[today_index]
    tomorrow_person = roommates[tomorrow_index]

    title = f"🚨 {dorm_id}宿舍倒垃圾警报！"
    content = f"""
### 👑 今日倒垃圾大元帅：【{today_person}】
请速速清空垃圾桶，不要逼兄弟们求你！

---
🔜 明天准备接客的是：【{tomorrow_person}】<br>

<font color="#808080" size="2">*(本通知由宿舍云端物理超度系统 3.1.2 自动发送)*</font>
"""
    execute_pushplus_notice(push_token, push_topic, title, content)

if __name__ == "__main__":
    main()
