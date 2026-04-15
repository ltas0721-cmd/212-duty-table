import streamlit as st
import datetime
from supabase import create_client, Client

# 1. 基础配置
st.set_page_config(page_title="212宿舍值日系统 3.1.2", page_icon="🛡️")

# 2. 注入 CSS 修复标题换行问题
st.markdown(
    """
    <style>
    /* 针对电脑端大屏幕：强制标题一行显示 */
    .stApp h1 {
        white-space: nowrap !important;
        font-size: 2.2rem !important; /* 稍微缩小默认字号 */
        overflow: hidden;
        text-overflow: ellipsis;
    }
    
    /* 针对手机端小屏幕：允许换行并自动缩小字号，防止溢出 */
    @media (max-width: 640px) {
        .stApp h1 {
            white-space: normal !important;
            font-size: 1.6rem !important;
            line-height: 1.2;
        }
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("🗑️ 宿舍倒垃圾排班表 (全栈 3.1.2 版)")

# 3. 初始化 Supabase 客户端与环境变量
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    admin_password = st.secrets.get("ADMIN_PASSWORD", "212admin")
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("🚨 数据库连接失败，请检查系统环境变量配置。")
    st.stop()

# 4. 数据读取与前端缓存策略
@st.cache_data(ttl=600)
def get_dorm_data(dorm_id: str):
    try:
        res = supabase.table("dorm_rules").select("*").eq("dorm_id", dorm_id).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        st.error(f"🚨 数据库查询异常: {e}")
        return None

dorm_id = "212"  
data = get_dorm_data(dorm_id)

# 5. 核心展示与算法渲染区
if data:
    roommates = [n.strip() for n in data["roommates"].split(",")]
    anchor_date = datetime.datetime.strptime(data["anchor_date"], "%Y-%m-%d").date()
    anchor_person = data["anchor_person"]

    selected_date = st.date_input("请选择查看日期：", datetime.date.today())
    days_diff = (selected_date - anchor_date).days
    num_people = len(roommates)
    
    if anchor_person in roommates:
        idx = roommates.index(anchor_person)
        today_p = roommates[(days_diff + idx) % num_people]
        tomorrow_p = roommates[(days_diff + 1 + idx) % num_people]
        
        st.success(f"👑 **{selected_date}** 倒垃圾大元帅：【**{today_p}**】")
        st.info(f"🔜 明天准备接客的是：【{tomorrow_p}】")
    else:
        st.error("🚨 数据异常：初始负责人不在当前名单中，请进入控制台修正。")
else:
    st.warning("⚠️ 数据库中未查询到该宿舍配置。")

# 6. 后台管理模块
st.markdown("---")
with st.expander("🔐 管理员控制台 (Admin Panel)"):
    pwd = st.text_input("请输入管理口令：", type="password")
    
    if pwd == admin_password:
        st.subheader("⚙️ 排班规则热更新")
        new_names = st.text_input("室友名单（请用英文逗号分隔）：", value=data["roommates"] if data else "")
        new_date = st.date_input("设置新锚点日期：", value=anchor_date if data else datetime.date.today())
        
        options_list = [n.strip() for n in new_names.split(",")] if new_names else []
        default_idx = options_list.index(anchor_person) if anchor_person in options_list else 0
        new_person = st.selectbox("选择新锚点负责人：", options=options_list, index=default_idx)

        if st.button("🚀 同步覆写至云端数据库"):
            try:
                supabase.table("dorm_rules").update({
                    "roommates": new_names,
                    "anchor_date": str(new_date),
                    "anchor_person": new_person
                }).eq("dorm_id", dorm_id).execute()
                
                st.cache_data.clear()  
                st.rerun()             
            except Exception as e:
                st.error(f"❌ 数据同步异常：{e}")
    elif pwd:
        st.error("🔑 权限校验失败，拒绝访问。")

st.caption("Powered by Streamlit & Supabase | 212 宿舍全栈数据中心 v3.1.2")
