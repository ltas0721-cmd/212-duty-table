import os
import datetime
import requests
from supabase import create_client, Client

def fetch_dorm_config(supabase: Client, dorm_id: str) -> dict:
    """从 Supabase 拉取指定宿舍的配置数据"""
    try:
        response = supabase.table("dorm_rules").select("*").eq("dorm_id", dorm_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"[Error] 数据库查询失败: {e}")
        return None

def execute_pushplus_notice(token: str, topic: str, title: str, content: str):
    """执行 PushPlus 消息推送请求"""
    url = "http://www.pushplus.plus/send"
    payload = {
        "token": token,
        "title": title,
        "content": content,
        "template": "markdown",
        "topic": topic
    }
    try:
        res = requests.post(url, json=payload)
        res.raise_for_status() # 检查 HTTP 请求是否成功
        print(f"[Success] PushPlus 推送成功: {res.json()}")
    except Exception as e:
        print(f"[Error] PushPlus 推送失败: {e}")

def main():
    # 1. 初始化环境变量与 Supabase 客户端
    sb_url = os.environ.get("SUPABASE_URL")
    sb_key = os.environ.get("SUPABASE_KEY")
    push_token = os.environ.get("PUSHPLUS_TOKEN")

    if not all([sb_url, sb_key, push_token]):
        print("[Fatal] 环境变量缺失，请检查 GitHub Actions Secrets 配置。")
        return

    supabase: Client = create_client(sb_url, sb_key)
    dorm_id = "212"  # 预留扩展: 未来可遍历数据库中所有活跃宿舍执行推送

    # 2. 获取并解析排班配置
    data = fetch_dorm_config(supabase, dorm_id)
    if not data:
        print(f"[Warning] 未获取到 {dorm_id} 宿舍的有效配置，跳过推送。")
        return

    roommates = [name.strip() for name in data["roommates"].split(",")]
    anchor_date = datetime.datetime.strptime(data["anchor_date"], "%Y-%m-%d").date()
    anchor_person = data["anchor_person"]
    push_topic = data["pushplus_topic"]

    # 数据一致性校验
    if anchor_person not in roommates:
        print(f"[Fatal] 初始人 '{anchor_person}' 不在名单中，请核对数据库记录。")
        return

    # 3. 核心排班算法
    today = datetime.date.today()
    days_passed = (today - anchor_date).days
    num_people = len(roommates)

    anchor_index = roommates.index(anchor_person)
    today_index = (days_passed + anchor_index) % num_people
    tomorrow_index = (days_passed + 1 + anchor_index) % num_people

    today_person = roommates[today_index]
    tomorrow_person = roommates[tomorrow_index]

    # 4. 构建并发送消息
    title = f"🚨 {dorm_id}宿舍倒垃圾警报！"
    content = f"""
### 👑 今日倒垃圾大元帅：【{today_person}】
请速速清空垃圾桶，不要逼兄弟们求你！

---
🔜 明天准备接客的是：【{tomorrow_person}】<br>

<font color="#808080" size="2">*(本通知由宿舍云端物理超度系统 3.0 自动发送)*</font>
"""
    
    execute_pushplus_notice(push_token, push_topic, title, content)

if __name__ == "__main__":
    main()
