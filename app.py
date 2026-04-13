import streamlit as st
import datetime

st.title("🗑️ 212宿舍倒垃圾排班表")

def get_duty_person():
    # 固定的轮换顺序
    roommates = ["李名伟", "王晟", "郑加裕", "陈镇灿"]
    num_people = len(roommates)

    # ====== 放假回来后，只需要修改以下两行 ======
    
    # 1. 修改为回宿舍、重新开始排班的那一天
    anchor_date = datetime.date(2026, 5, 5) # 假设五一假期5月5日回来
    
    # 2. 修改回宿舍这一天，决定由谁先开始倒垃圾（必须是上面四个名字之一）
    anchor_person = "郑加裕" 
    
    # ================================================
    
    # 获取这个基准人在列表里的初始位置 (0, 1, 2, 3)
    anchor_index = roommates.index(anchor_person)
    
    selected_date = st.date_input("请选择你想查看的日期：", datetime.date.today())
    
    # 计算经过的天数（过去的日子会变成负数，不影响排班逻辑）
    days_passed = (selected_date - anchor_date).days
    
    # 核心算法升级：加上了“锚点人”的偏移量
    today_index = (days_passed + anchor_index) % num_people
    tomorrow_index = (days_passed + 1 + anchor_index) % num_people
    
    today_person = roommates[today_index]
    tomorrow_person = roommates[tomorrow_index]
    
    st.success(f"👑 **{selected_date}** 倒垃圾大元帅：【**{today_person}**】")
    st.info(f"🔜 明天准备接客的是：【{tomorrow_person}】")

if __name__ == "__main__":
    get_duty_person()
