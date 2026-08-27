import datetime
from typing import Optional

import streamlit as st
from supabase import Client, create_client


st.set_page_config(
    page_title="212 值日表",
    page_icon="🗓️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;600;700&display=swap');
    :root { --paper:#f5f1e8; --ink:#25231f; --muted:#746f66; --line:#ded7ca; --accent:#c65d3a; --accent-soft:#f1ddd3; --card:#fffdf8; }
    .stApp { background:var(--paper); color:var(--ink); font-family:'Noto Sans SC',-apple-system,BlinkMacSystemFont,sans-serif; }
    [data-testid="stHeader"] { background:transparent; }
    [data-testid="stToolbar"] { visibility:hidden; height:0; }
    .block-container { max-width:760px; padding:3.5rem 1.25rem 3rem; }
    .eyebrow { color:var(--accent); font-size:.78rem; font-weight:700; letter-spacing:.16em; margin-bottom:.7rem; text-transform:uppercase; }
    .page-title { color:var(--ink); font-size:clamp(2rem,7vw,3.35rem); font-weight:700; letter-spacing:-.06em; line-height:1.08; margin:0; }
    .page-subtitle { color:var(--muted); font-size:.98rem; margin:.85rem 0 2.2rem; }
    .today-card { background:var(--card); border:1px solid var(--line); border-radius:18px; box-shadow:0 12px 35px rgba(61,47,30,.07); padding:1.55rem 1.65rem 1.7rem; }
    .card-label { color:var(--muted); font-size:.8rem; letter-spacing:.08em; margin-bottom:.45rem; }
    .date-line { color:var(--ink); font-size:1.05rem; font-weight:600; }
    .duty-name { color:var(--accent); font-size:clamp(2.5rem,13vw,5.2rem); font-weight:700; letter-spacing:-.08em; line-height:1; margin:1.3rem 0 1.35rem; word-break:keep-all; }
    .tomorrow { border-top:1px solid var(--line); color:var(--muted); font-size:.95rem; padding-top:1rem; }
    .tomorrow strong { color:var(--ink); font-weight:600; }
    .empty-card { background:var(--accent-soft); border:1px solid #e7c8bb; border-radius:14px; color:#7d3d2c; padding:1rem 1.15rem; }
    .section-caption { color:var(--muted); font-size:.82rem; margin:1.5rem 0 .55rem; }
    div[data-testid="stDateInput"] label, div[data-testid="stTextInput"] label, div[data-testid="stSelectbox"] label { color:var(--muted); }
    div[data-baseweb="input"] > div, div[data-baseweb="select"] > div { background:var(--card); border-color:var(--line); color:var(--ink); }
    div[data-baseweb="input"] input { color:var(--ink); }
    div[data-testid="stExpander"] { background:rgba(255,253,248,.55); border:1px solid var(--line); border-radius:14px; }
    .footer-note { color:#979084; font-size:.78rem; margin-top:2.25rem; text-align:center; }
    @media (max-width:640px) { .block-container { padding-top:2.2rem; } .today-card { padding:1.25rem 1.2rem 1.35rem; } }
    </style>
    """,
    unsafe_allow_html=True,
)


def format_date(value: datetime.date) -> str:
    weekdays = "一二三四五六日"
    return f"{value:%Y年%m月%d日} · 星期{weekdays[value.weekday()]}"


st.markdown('<div class="eyebrow">ROOM 212 · DUTY BOARD</div>', unsafe_allow_html=True)
st.markdown('<h1 class="page-title">今天，谁倒垃圾？</h1>', unsafe_allow_html=True)
st.markdown('<p class="page-subtitle">一个不靠猜的宿舍值日表。选日期，马上知道该谁了。</p>', unsafe_allow_html=True)

try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    service_key = st.secrets.get("SUPABASE_SERVICE_ROLE_KEY")
    admin_password = st.secrets.get("ADMIN_PASSWORD", "212admin")
    supabase: Client = create_client(url, key)
    admin_supabase: Optional[Client] = create_client(url, service_key) if service_key else None
except Exception:
    st.markdown('<div class="empty-card">暂时连不上云端数据库。请在 Supabase 控制台确认项目已恢复，并检查 Streamlit Secrets。</div>', unsafe_allow_html=True)
    st.stop()


@st.cache_data(ttl=600)
def get_dorm_data(dorm_id: str):
    try:
        response = supabase.table("dorm_rules").select("*").eq("dorm_id", dorm_id).execute()
        return response.data[0] if response.data else None
    except Exception as error:
        st.warning(f"暂时无法读取云端排班数据：{error}")
        return None


dorm_id = "212"
data = get_dorm_data(dorm_id)

if data:
    roommates = [name.strip() for name in str(data.get("roommates", "")).split(",") if name.strip()]
    anchor_person = str(data.get("anchor_person", "")).strip()
    try:
        anchor_date = datetime.datetime.strptime(str(data["anchor_date"]), "%Y-%m-%d").date()
    except (KeyError, TypeError, ValueError):
        anchor_date = None

    selected_date = st.date_input("查看其他日期", value=datetime.date.today(), format="YYYY-MM-DD")

    if not roommates or anchor_date is None:
        st.markdown('<div class="empty-card">云端排班配置还不完整，请打开下方管理员面板检查名单和锚点日期。</div>', unsafe_allow_html=True)
    elif anchor_person not in roommates:
        st.markdown('<div class="empty-card">锚点负责人不在当前室友名单中，请打开下方管理员面板修正。</div>', unsafe_allow_html=True)
    else:
        index = roommates.index(anchor_person)
        days_diff = (selected_date - anchor_date).days
        today_person = roommates[(days_diff + index) % len(roommates)]
        tomorrow_person = roommates[(days_diff + index + 1) % len(roommates)]
        st.markdown(
            f'<section class="today-card"><div class="card-label">{format_date(selected_date)}</div><div class="date-line">今日值日</div><div class="duty-name">{today_person}</div><div class="tomorrow">明天接班：<strong>{tomorrow_person}</strong></div></section>',
            unsafe_allow_html=True,
        )
else:
    st.markdown('<div class="empty-card">数据库中还没有 212 宿舍的排班配置。</div>', unsafe_allow_html=True)


st.markdown('<div class="section-caption">只有需要改名单或日期时，才打开这里</div>', unsafe_allow_html=True)
with st.expander("管理员面板"):
    password = st.text_input("管理密码", type="password")

    if password == admin_password:
        st.caption("修改会直接写入云端数据库。")
        current_names = data.get("roommates", "") if data else ""
        current_date = (anchor_date or datetime.date.today()) if data else datetime.date.today()
        new_names = st.text_input("室友名单（用英文逗号分隔）", value=current_names)
        new_date = st.date_input("锚点日期", value=current_date, format="YYYY-MM-DD")
        options = [name.strip() for name in new_names.split(",") if name.strip()]
        current_anchor = str(data.get("anchor_person", "")).strip() if data else ""

        if options:
            default_index = options.index(current_anchor) if current_anchor in options else 0
            new_person = st.selectbox("锚点负责人", options=options, index=default_index)
        else:
            new_person = ""
            st.warning("请至少填写一位室友。")

        if st.button("保存排班", type="primary", disabled=not options or not new_person):
            if admin_supabase is None:
                st.error("未配置 SUPABASE_SERVICE_ROLE_KEY，暂时不能安全地写入数据。")
            else:
                try:
                    admin_supabase.table("dorm_rules").update({"roommates": ",".join(options), "anchor_date": str(new_date), "anchor_person": new_person}).eq("dorm_id", dorm_id).execute()
                    st.cache_data.clear()
                    st.success("已保存，正在刷新页面。")
                    st.rerun()
                except Exception as error:
                    st.error(f"保存失败：{error}")
    elif password:
        st.error("密码不正确。")


st.markdown('<div class="footer-note">212 宿舍 · 轮流值日，少一点争论</div>', unsafe_allow_html=True)
