import datetime
from html import escape
from typing import Dict, List, Optional, Tuple

import streamlit as st
from supabase import Client, create_client
from schedule import person_for_date, week_schedule


st.set_page_config(
    page_title="212 宿舍值日",
    page_icon="🗓️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;600;700;800&display=swap');
    :root {
        --bg: #f8f7f1;
        --surface: #fffefa;
        --surface-soft: #f0eee5;
        --mint: #dff3dc;
        --green: #42b653;
        --green-deep: #227c37;
        --ink: #20231f;
        --muted: #70766c;
        --line: #e2e0d8;
        --coral: #d9574b;
    }
    .stApp { background: var(--bg); color: var(--ink); font-family: 'Noto Sans SC', -apple-system, BlinkMacSystemFont, sans-serif; }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stToolbar"] { visibility: hidden; height: 0; }
    .block-container { max-width: 1180px; padding: 1.5rem 2rem 3.5rem; }
    .nav-shell { align-items: center; background: var(--surface); border: 1px solid var(--line); border-radius: 16px; box-shadow: 0 5px 18px rgba(40,48,35,.05); display: flex; gap: 1.5rem; justify-content: space-between; margin-bottom: 4.5rem; padding: .85rem 1.15rem; }
    .brand { align-items: center; color: var(--ink); display: flex; font-size: .95rem; font-weight: 800; gap: .55rem; white-space: nowrap; }
    .brand-mark { align-items: center; background: var(--green); border-radius: 9px; color: white; display: inline-flex; font-size: .8rem; height: 30px; justify-content: center; width: 30px; }
    .nav-links { display: flex; gap: 1.4rem; margin-right: auto; }
    .nav-links a { color: var(--muted); font-size: .84rem; text-decoration: none; }
    .nav-links a:hover { color: var(--green-deep); }
    .online-pill { align-items: center; color: var(--green-deep); display: flex; font-size: .76rem; gap: .4rem; white-space: nowrap; }
    .online-dot { background: var(--green); border-radius: 50%; height: 7px; width: 7px; }
    .eyebrow { color: var(--green-deep); font-size: .76rem; font-weight: 800; letter-spacing: .16em; margin-bottom: .75rem; text-transform: uppercase; }
    .hero-title { color: var(--ink); font-size: clamp(2.15rem, 5vw, 4.1rem); font-weight: 800; letter-spacing: -.075em; line-height: 1.04; margin: 0; }
    .hero-copy { color: var(--muted); font-size: 1rem; line-height: 1.7; margin: 1rem 0 2rem; max-width: 32rem; }
    .schedule-card, .side-card { background: var(--surface); border: 1px solid var(--line); border-radius: 16px; box-shadow: 0 8px 24px rgba(40,48,35,.07); }
    .schedule-card { min-height: 300px; padding: 1.5rem 1.65rem 1.6rem; }
    .schedule-label { color: var(--muted); font-size: .75rem; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; }
    .schedule-date { color: var(--ink); font-size: 1.05rem; font-weight: 600; margin-top: .45rem; }
    .schedule-name { color: var(--green-deep); font-size: clamp(3rem, 7vw, 5.3rem); font-weight: 800; letter-spacing: -.1em; line-height: .98; margin: 2rem 0 2.1rem; }
    .schedule-next { border-top: 1px solid var(--line); color: var(--muted); font-size: .9rem; padding-top: 1rem; }
    .schedule-next strong { color: var(--ink); font-weight: 700; }
    .side-card { padding: 1.2rem 1.25rem; }
    .side-card + .side-card { margin-top: 1rem; }
    .side-title { color: var(--ink); font-size: 1rem; font-weight: 700; margin-bottom: .75rem; }
    .side-copy { color: var(--muted); font-size: .83rem; line-height: 1.6; }
    .week-list { display: grid; gap: .45rem; }
    .week-row { align-items: center; border-bottom: 1px solid var(--line); display: flex; font-size: .8rem; justify-content: space-between; padding: .42rem 0; }
    .week-row:last-child { border-bottom: 0; padding-bottom: 0; }
    .week-day { color: var(--muted); }
    .week-person { color: var(--ink); font-weight: 600; }
    .intro-band { background: var(--mint); border-radius: 18px; margin-top: 5rem; padding: 2.5rem 2.2rem 2.7rem; }
    .section-kicker { color: var(--green-deep); font-size: .73rem; font-weight: 800; letter-spacing: .14em; text-transform: uppercase; }
    .section-title { color: var(--ink); font-size: clamp(1.6rem, 3vw, 2.15rem); font-weight: 800; letter-spacing: -.045em; margin: .55rem 0 1.8rem; }
    .info-grid { display: grid; gap: 1.15rem; grid-template-columns: repeat(3, 1fr); }
    .info-item { align-items: flex-start; display: flex; gap: 1rem; }
    .info-icon { align-items: center; background: var(--surface); border-radius: 13px; color: var(--green-deep); display: flex; flex: 0 0 48px; height: 48px; justify-content: center; }
    .info-icon svg { height: 25px; width: 25px; }
    .info-title { color: var(--ink); font-size: .94rem; font-weight: 700; margin-bottom: .35rem; }
    .info-copy { color: #586057; font-size: .82rem; line-height: 1.65; }
    .admin-section { margin-top: 4rem; }
    .admin-card { background: var(--surface-soft); border: 1px solid var(--line); border-radius: 16px; padding: 1.5rem 1.7rem; }
    .admin-heading { color: var(--ink); font-size: 1.25rem; font-weight: 800; margin: 0 0 .35rem; }
    .admin-copy { color: var(--muted); font-size: .86rem; margin: 0; }
    div[data-testid="stDateInput"] label, div[data-testid="stTextInput"] label, div[data-testid="stSelectbox"] label { color: var(--muted); font-size: .78rem; }
    div[data-baseweb="input"] > div, div[data-baseweb="select"] > div { background: var(--surface); border-color: var(--line); border-radius: 9px; color: var(--ink); min-height: 44px; }
    div[data-baseweb="input"] input { color: var(--ink); }
    div[data-testid="stButton"] button { border-radius: 9px; min-height: 44px; }
    div[data-testid="stExpander"] { background: transparent; border: 0; margin-top: 1rem; }
    div[data-testid="stExpander"] summary { color: var(--ink); font-weight: 700; }
    .empty-card { background: #f8e4df; border: 1px solid #ebc4ba; border-radius: 12px; color: #863e32; padding: 1rem 1.1rem; }
    .footer-note { color: #9a9d93; font-size: .76rem; margin-top: 3.2rem; text-align: center; }
    @media (max-width: 760px) {
        .block-container { padding: .9rem 1rem 2.5rem; }
        .nav-shell { border-radius: 12px; flex-wrap: wrap; gap: .7rem 1rem; margin-bottom: 2.8rem; padding: .75rem .9rem; }
        .nav-links { gap: .95rem; order: 3; overflow-x: auto; width: 100%; }
        .online-pill { margin-left: auto; }
        .hero-copy { font-size: .92rem; margin-bottom: 1.5rem; }
        .schedule-card { min-height: 260px; padding: 1.25rem 1.2rem 1.3rem; }
        .schedule-name { margin: 1.65rem 0 1.7rem; }
        .intro-band { margin-top: 3.2rem; padding: 1.7rem 1.1rem 1.8rem; }
        .info-grid { grid-template-columns: 1fr; }
        .admin-section { margin-top: 2.8rem; }
        .admin-card { padding: 1.2rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def format_date(value: datetime.date) -> str:
    weekdays = "一二三四五六日"
    return f"{value:%Y年%m月%d日} · 星期{weekdays[value.weekday()]}"


def parse_config(data: Optional[dict]) -> Tuple[List[str], Optional[datetime.date], str]:
    if not data:
        return [], None, ""
    names = [name.strip() for name in str(data.get("roommates", "")).split(",") if name.strip()]
    person = str(data.get("anchor_person", "")).strip()
    try:
        date_value = datetime.datetime.strptime(str(data["anchor_date"]), "%Y-%m-%d").date()
    except (KeyError, TypeError, ValueError):
        date_value = None
    return names, date_value, person


st.markdown(
    '<div id="home" class="nav-shell"><div class="brand"><span class="brand-mark">212</span><span>宿舍值日</span></div><nav class="nav-links"><a href="#home">值日表</a><a href="#about">怎么用</a><a href="#admin">管理员</a></nav><div class="online-pill"><span class="online-dot"></span>云端在线</div></div>',
    unsafe_allow_html=True,
)

st.markdown('<div class="eyebrow">ROOM 212 · DUTY BOARD</div>', unsafe_allow_html=True)
st.markdown('<h1 class="hero-title">Welcome back, 212!</h1>', unsafe_allow_html=True)
st.markdown('<p class="hero-copy">今天，谁负责把垃圾带走？<br>选一个日期，马上知道该谁了。</p>', unsafe_allow_html=True)

try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    service_key = st.secrets.get("SUPABASE_SERVICE_ROLE_KEY")
    admin_password = st.secrets.get("ADMIN_PASSWORD", "212admin")
    supabase: Client = create_client(url, key)
    admin_supabase: Optional[Client] = create_client(url, service_key) if service_key else None
except Exception:
    st.markdown('<div class="empty-card">暂时连不上云端数据库，请检查 Supabase 项目状态和 Streamlit Secrets。</div>', unsafe_allow_html=True)
    st.stop()


@st.cache_data(ttl=600)
def get_dorm_data(dorm_id: str):
    try:
        result = supabase.table("dorm_rules").select("*").eq("dorm_id", dorm_id).execute()
        return result.data[0] if result.data else None
    except Exception as error:
        st.warning(f"暂时无法读取云端排班数据：{error}")
        return None


dorm_id = "212"
data = get_dorm_data(dorm_id)
roommates, anchor_date, anchor_person = parse_config(data)
try:
    skip_rows = supabase.table("duty_skips").select("id, roommate, start_date, skip_count, created_at, active").eq("dorm_id", dorm_id).eq("active", True).order("start_date").execute().data or []
except Exception:
    skip_rows = []

if data and roommates and anchor_date and anchor_person in roommates:
    left, right = st.columns([1.55, 1], gap="large")
    with right:
        selected_date = st.date_input("选择查看日期", value=datetime.date.today(), format="YYYY-MM-DD")
        st.markdown('<div class="side-card"><div class="side-title">本周排班</div><div class="side-copy">从选定日期起的 7 天，提前看一眼。</div></div>', unsafe_allow_html=True)
        week_rows = []
        for day_offset in range(7):
            day_value = selected_date + datetime.timedelta(days=day_offset)
            person = person_for_date(day_value, anchor_date, roommates, anchor_person, skip_rows)
            week_rows.append(f'<div class="week-row"><span class="week-day">{day_value:%m/%d} · {"今天" if day_offset == 0 else "周" + "一二三四五六日"[day_value.weekday()]}</span><span class="week-person">{escape(person)}</span></div>')
        st.markdown(f'<div class="side-card"><div class="week-list">{"".join(week_rows)}</div></div>', unsafe_allow_html=True)
    with left:
        today_person = person_for_date(selected_date, anchor_date, roommates, anchor_person, skip_rows)
        tomorrow_person = person_for_date(selected_date + datetime.timedelta(days=1), anchor_date, roommates, anchor_person, skip_rows)
        st.markdown(
            f'<section class="schedule-card"><div class="schedule-label">今日值日</div><div class="schedule-date">{escape(format_date(selected_date))}</div><div class="schedule-name">{escape(today_person)}</div><div class="schedule-next">明天接班：<strong>{escape(tomorrow_person)}</strong></div></section>',
            unsafe_allow_html=True,
        )
else:
    st.markdown('<div class="empty-card">暂时没有完整的 212 宿舍排班配置，请稍后再试或联系管理员。</div>', unsafe_allow_html=True)


st.markdown('<div class="side-card" style="margin-top:1.25rem"><div class="side-title">临时轮空</div><div class="side-copy">要回家几天？标记后，排班会自动顺延。</div></div>', unsafe_allow_html=True)
if roommates:
    skip_left, skip_mid, skip_right = st.columns([1.2, 1.1, .8])
    with skip_left:
        skip_person = st.selectbox("谁轮空", options=roommates, key="skip_person")
    with skip_mid:
        skip_start = st.date_input("从哪天开始", value=datetime.date.today(), key="skip_start", format="YYYY-MM-DD")
    with skip_right:
        skip_count = st.number_input("轮空次数", min_value=1, max_value=30, value=1, step=1, key="skip_count")
    if st.button("提交轮空标记", key="submit_skip"):
        try:
            supabase.table("duty_skips").insert({"dorm_id": dorm_id, "roommate": skip_person, "start_date": str(skip_start), "skip_count": int(skip_count)}).execute()
            st.cache_data.clear()
            st.success(f"已记录：{skip_person} 从 {skip_start} 起轮空 {skip_count} 次。")
            st.rerun()
        except Exception as error:
            st.error(f"提交失败，请确认已创建 duty_skips 表：{error}")
    if skip_rows:
        active_text = " · ".join(f"{row.get('roommate')}（{row.get('start_date')}，{row.get('skip_count')} 次）" for row in skip_rows)
        st.caption(f"当前生效：{active_text}")


st.markdown(
    '''<section id="about" class="intro-band"><div class="section-kicker">A SMALL ROUTINE, LESS ARGUMENT</div><h2 class="section-title">接下来？</h2><div class="info-grid"><div class="info-item"><div class="info-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 20V7.5L12 3l8 4.5V20"/><path d="M8 20v-6h8v6M9 9h.01M15 9h.01"/></svg></div><div><div class="info-title">看一眼就知道</div><div class="info-copy">打开页面，今天和明天的值日人清清楚楚。</div></div></div><div class="info-item"><div class="info-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="4" y="5" width="16" height="15" rx="2"/><path d="M8 3v4M16 3v4M4 10h16M8 14h3M8 17h5"/></svg></div><div><div class="info-title">每天自动同步</div><div class="info-copy">云端排班和每日提醒自动运行，不用在群里反复确认。</div></div></div><div class="info-item"><div class="info-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M18 9a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4"/></svg></div><div><div class="info-title">有变化随时调整</div><div class="info-copy">搬寝、换班或日期变化时，管理员可以直接更新。</div></div></div></div></section>''',
    unsafe_allow_html=True,
)


st.markdown('<section id="admin" class="admin-section"><div class="admin-card"><h2 class="admin-heading">管理排班</h2><p class="admin-copy">仅管理员使用。修改会直接写入云端数据库。</p></div></section>', unsafe_allow_html=True)
with st.expander("打开管理员入口"):
    password = st.text_input("管理密码", type="password")
    if password == admin_password:
        if skip_rows:
            st.markdown("**轮空记录管理**")
            for row in skip_rows:
                row_id = row.get("id")
                if st.button(f"撤销 {row.get('roommate')} · {row.get('start_date')}", key=f"revoke_{row_id}"):
                    if admin_supabase is None:
                        st.error("未配置 SUPABASE_SERVICE_ROLE_KEY，不能撤销记录。")
                    else:
                        admin_supabase.table("duty_skips").update({"active": False}).eq("id", row_id).execute()
                        st.cache_data.clear()
                        st.rerun()
        current_names = data.get("roommates", "") if data else ""
        current_date = anchor_date or datetime.date.today()
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
