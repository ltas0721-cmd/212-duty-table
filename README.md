# 212 宿舍值日表

一个给 212 宿舍用的值日小工具：打开网页就能看到今天谁倒垃圾，临时回家时也能标记轮空，系统会自动把后面的排班顺延。

## 现在能做什么

- **首页排班**：显示今日值日人、明日接班人和未来 7 天安排。
- **日期查询**：选择任意日期，查看当天对应的值日人。
- **临时轮空**：舍友回家或暂时不在时，选择开始日期和轮空次数，排班自动顺延。
- **自动提醒**：GitHub Actions 每天按北京时间运行，通过 PushPlus 发送提醒。
- **管理员面板**：使用管理密码修改名单、锚点日期、负责人，并撤销错误的轮空记录。
- **响应式页面**：桌面端双栏展示，手机端自动改为单栏布局。

## 轮空规则

轮空不会删除舍友的值日责任，只会把责任暂时往后推。

- 标记 1 次：跳过下一次轮到自己的日期，之后正常值日。
- 标记 2 次：跳过两次轮换，之后连续值日 2 天。
- 标记 3 次：跳过三次轮换，之后连续值日 3 天。

轮空记录保存在 `duty_skips` 表中，网页和每日通知使用同一套排班算法。

## 技术栈

- Python 3.9+
- Streamlit
- Supabase PostgreSQL
- GitHub Actions
- PushPlus
- `chinesecalendar`

## 项目文件

- `app.py`：Streamlit 页面、日期查询、轮空提交和管理员面板。
- `notify.py`：GitHub Actions 使用的每日提醒脚本。
- `schedule.py`：网页与通知共享的排班和顺延算法。
- `schema.sql`：创建 `duty_skips` 表及 RLS 策略。
- `.github/workflows/clock.yml`：每日定时任务。

## 部署步骤

### 1. 创建数据库表

在 Supabase SQL Editor 中执行 `schema.sql`。原有的 `dorm_rules` 表和数据不会被删除。

### 2. Supabase RLS

`dorm_rules` 至少需要允许 `anon` 和 `authenticated` 读取；`duty_skips` 的读取和新增策略已包含在 `schema.sql` 中。

不要给 `anon` 开放修改或删除已有轮空记录的权限。

### 3. Streamlit Secrets

```toml
SUPABASE_URL = "https://你的项目.supabase.co"
SUPABASE_KEY = "你的 anon key"
SUPABASE_SERVICE_ROLE_KEY = "你的 service_role key"
ADMIN_PASSWORD = "你的管理员密码"
```

`SUPABASE_SERVICE_ROLE_KEY` 只放在 Streamlit Secrets，不要提交到 GitHub，也不要发到聊天中。

### 4. GitHub Actions Secrets

在仓库的 `Settings → Secrets and variables → Actions` 中添加：

```text
SUPABASE_URL
SUPABASE_KEY
PUSHPLUS_TOKEN
```

定时任务使用北京时间计算日期。工作流每天 UTC 23:05 运行，对应北京时间次日 07:05 左右。

## 运行逻辑

网页和通知脚本都会读取 `dorm_rules` 与当前有效的 `duty_skips`，从锚点日期开始逐日模拟排班。遇到有效轮空记录时，系统跳过该舍友并保留他的值日责任；轮空次数耗尽后，累计责任会转换为连续值日天数。

项目在寒暑假期间保持轻量数据库保活，但不会发送值日提醒；普通周末照常运行。法定节假日由 `chinesecalendar` 判断。

## 本地检查

```bash
python3 -m py_compile app.py notify.py schedule.py
python3 test_schedule.py
```

> 由 212 宿舍维护。少一点争论，多一点按时倒垃圾。
