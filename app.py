import streamlit as st
import datetime

# 网页的标题
st.title("🗑️ 212宿舍倒垃圾排班表")

def get_duty_person():
    roommates = ["李名伟", "王晟", "郑加裕", "陈镇灿"]
    num_people = len(roommates)
    anchor_date = datetime.date(2026, 4, 13) 
    
    # 增加一个炫酷的日期选择器，默认今天是今天
    selected_date = st.date_input("请选择你想查看的日期：", datetime.date.today())
    
    days_passed = (selected_date - anchor_date).days
    
    if days_passed < 0:
        st.error("设定的基准日期在未来，别乱选时间旅行哦！")
        return
        
    # Python 的 % 运算对负数也很友好，但我们上面的逻辑限制了不能选过去
    today_index = days_passed % num_people
    tomorrow_index = (days_passed + 1) % num_people
    
    today_person = roommates[today_index]
    tomorrow_person = roommates[tomorrow_index]
    
    # 用醒目的卡片展示结果
    st.success(f"👑 **{selected_date}** 倒垃圾大元帅：【**{today_person}**】")
    st.info(f"🔜 明天准备接客的是：【{tomorrow_person}】")

if __name__ == "__main__":
    get_duty_person()