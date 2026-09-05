import os
import datetime
import requests
import chinese_calendar as calendar
from supabase import create_client, Client
from zoneinfo import ZoneInfo
from schedule import person_for_date

def fetch_dorm_config(supabase: Client, dorm_id: str) -> dict:
    try:
        response = supabase.table("dorm_rules").select("*").eq("dorm_id", dorm_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"[Error] 数据库查询失败: {e}")
        return None

def keep_database_alive(supabase: Client) -> bool:
    """Perform a tiny read so Supabase free projects do not go idle during breaks."""
    try:
        supabase.table("dorm_rules").select("dorm_id").limit(1).execute()
        return True
    except Exception as e:
        print(f"[Error] 云端保活查询失败: {e}")
        return False

def execute_pushplus_notice(token: str, topic: str, title: str, content: str):
    url = "https://www.pushplus.plus/send"
    payload = {"token": token, "title": title, "content": content, "template": "markdown", "topic": topic}
    try:
        res = requests.post(url, json=payload, timeout=20)
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

    # 使用带时区的时间，避免依赖 GitHub runner 的本地时区。
    today = datetime.datetime.now(ZoneInfo("Asia/Shanghai")).date()

    supabase: Client = create_client(sb_url, sb_key)
    dorm_id = "212"

    # Supabase 免费计划会因长期无请求自动暂停。即使是假期，也先做一次
    # 轻量查询维持数据库活跃，再决定是否发送通知。
    if not keep_database_alive(supabase):
        return

    # ====== 1. 寒暑假区间拦截 ======
    month = today.month
    day = today.day

    is_summer_vacation = (month == 7 and day >= 11) or (month == 8 and day <= 29)  # 7月11日~8月29日
    is_winter_vacation = (month == 1 and day >= 15) or (month == 2 and day <= 20)  # 1月15日~2月20日

    if is_summer_vacation or is_winter_vacation:
        print(f"[Info] 北京时间 {today} 属于寒暑假期间，系统休眠。")
        return

    # ====== 2. 原有的法定节假日拦截 ======
    on_holiday, holiday_name = calendar.get_holiday_detail(today)
    
    if on_holiday and holiday_name is not None:
        print(f"[Info] 北京时间 {today} 是 {holiday_name}，系统休眠。")
        return
    # -----------------------------------------------------------------

    data = fetch_dorm_config(supabase, dorm_id)
    if not data:
        print("[Warning] 未获取到配置。")
        return

    roommates = [name.strip() for name in str(data.get("roommates", "")).split(",") if name.strip()]
    if not roommates:
        print("[Fatal] 室友名单为空。")
        return
    try:
        anchor_date = datetime.datetime.strptime(str(data["anchor_date"]), "%Y-%m-%d").date()
    except (KeyError, TypeError, ValueError) as e:
        print(f"[Fatal] 锚点日期无效: {e}")
        return
    anchor_person = str(data.get("anchor_person", "")).strip()
    push_topic = str(data.get("pushplus_topic", "")).strip()

    if anchor_person not in roommates:
        print(f"[Fatal] 初始人不在名单中。")
        return

    try:
        skip_rows = supabase.table("duty_skips").select("roommate, start_date, skip_count, active").eq("dorm_id", dorm_id).eq("active", True).execute().data or []
    except Exception as e:
        print(f"[Warning] 轮空记录读取失败，将按普通排班发送: {e}")
        skip_rows = []

    today_person = person_for_date(today, anchor_date, roommates, anchor_person, skip_rows)
    tomorrow_person = person_for_date(today + datetime.timedelta(days=1), anchor_date, roommates, anchor_person, skip_rows)

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
