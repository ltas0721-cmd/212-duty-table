import os
import datetime
import requests

def send_wechat_notice():
    # 1. 照搬你的排班核心逻辑
    roommates = ["李名伟", "王晟", "郑加裕", "陈镇灿"]
    anchor_date = datetime.date(2026, 4, 13) 
    anchor_person = "李名伟" # 填你们现在的起始人
    
    today = datetime.date.today()
    days_passed = (today - anchor_date).days
    anchor_index = roommates.index(anchor_person)
    
    today_index = (days_passed + anchor_index) % len(roommates)
    tomorrow_index = (days_passed + 1 + anchor_index) % len(roommates)
    
    today_person = roommates[today_index]
    tomorrow_person = roommates[tomorrow_index]
    
    # 2. 准备骚话文案
    title = "🚨 212宿舍倒垃圾警报！"
    content = f"""
    ### 👑 今日倒垃圾大元帅：【{today_person}】
    请速速清空垃圾桶，不要逼兄弟们求你！
    
    ---
    🔜 明天准备接客的是：【{tomorrow_person}】
    （本通知由宿舍云端物理超度系统自动发送）
    """
    
    # 3. 从环境变量获取刚才的 Token (为了安全，不写死在代码里)
    token = os.environ.get("PUSHPLUS_TOKEN")
    
    if not token:
        print("没找到 Token，没法发消息啦！")
        return

    # 4. 发送请求给 PushPlus
    url = "http://www.pushplus.plus/send"
    data = {
        "token": token,
        "title": title,
        "content": content,
        "template": "markdown" # 支持好看的排版
    }
    
    response = requests.post(url, json=data)
    print(f"发送结果：{response.text}")

if __name__ == "__main__":
    send_wechat_notice()
