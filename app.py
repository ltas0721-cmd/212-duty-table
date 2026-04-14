import streamlit as st
import datetime
from supabase import create_client, Client

st.set_page_config(page_title="212宿舍倒垃圾排班系统 2.0", page_icon="🗑️")
st.title("🗑️ 宿舍倒垃圾排班表 (云端 2.0 版)")

# 初始化 Supabase 客户端
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("🚨 数据库连接失败，请检查环境变量配置。")
    st.stop()

# 缓存数据库请求，避免高并发下超额调用 API
@st.cache_data(ttl=600)
def get_dorm_data(dorm_id: str):
    try:
        response = supabase.table("dorm_rules").select("*").eq("dorm_id", dorm_id).execute()
        
        if response.data:
            data = response.data[0]
            roommates = [name.strip() for name in data["roommates"].split(",")]
            anchor_date = datetime.datetime.strptime(data["anchor_date"], "%Y-%m-%d").date()
            anchor_person = data["anchor_person"]
            return roommates, anchor_date, anchor_person
        return None, None, None
    except Exception as e:
        st.error(f"🚨 读取数据库时发生错误: {e}")
        return None, None, None

def show_duty_schedule():
    dorm_id = "212"  # 预留扩展接口：后续升级多用户时可改为前端输入
    roommates, anchor_date, anchor_person = get_dorm_data(dorm_id)

    if not roommates:
        st.warning(f"⚠️ 找不到宿舍 {dorm_id} 的排班记录。")
        return

    # 数据校验防呆设计
    if anchor_person not in roommates:
         st.error(f"🚨 错误：初始人 '{anchor_person}' 不在宿舍名单里！请检查数据库。")
         return
         
    anchor_index = roommates.index(anchor_person)
    selected_date = st.date_input("请选择你想查看的日期：", datetime.date.today())
    
    # 核心排班算法
    days_passed = (selected_date - anchor_date).days
    num_people = len(roommates)
    
    today_index = (days_passed + anchor_index) % num_people
    tomorrow_index = (days_passed + 1 + anchor_index) % num_people
    
    today_person = roommates[today_index]
    tomorrow_person = roommates[tomorrow_index]
    
    st.success(f"👑 **{selected_date}** 倒垃圾大元帅：【**{today_person}**】")
    st.info(f"🔜 明天准备接客的是：【{tomorrow_person}】")

if __name__ == "__main__":
    show_duty_schedule()
    
    st.markdown("---")
    st.caption("Powered by Supabase & Streamlit | 212 宿舍云端数据中心")
