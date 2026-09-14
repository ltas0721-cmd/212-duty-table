# 212 宿舍值日表

一个给 212 宿舍用的值日小工具：打开网页就知道今天谁倒垃圾。有人临时回家，可以标记轮空、之后补班；全宿舍今天都不需要值日时，管理员可以把后续安排整体往后移一天。

## 现在能做什么

- **首页排班**：显示今日值日人、明日接班人和未来 7 天安排。
- **日期查询**：选择任意日期，查看当天对应的值日人。
- **临时轮空**：舍友回家或暂时不在时，选择开始日期和轮空次数，排班自动顺延。
- **一键顺延一天**：管理员预览并确认后，当天暂停值日，后续安排整体后移，已有轮空和连续补班顺序保留。
- **自动提醒**：GitHub Actions 每天按北京时间运行，通过 PushPlus 发送提醒。
- **管理员面板**：使用管理密码修改名单、锚点日期、负责人，并撤销错误的轮空记录。
- **响应式页面**：桌面端双栏展示，手机端自动改为单栏布局。

## 排班怎么调整

### 管理员整体顺延

管理员入口新增“从今天起顺延一天”。预览七天变化并确认后，今天暂停，原排班和连续补班一起后移一天；历史不变。如果今天已经暂停，则在之后第一个非暂停日再暂停一天。未来已有轮空记录的开始日期同步移动，之后新提交的轮空按选择的实际日期生效。

例如，甲原本需要连续值日两天：

| 日期 | 原安排 | 顺延后 |
| --- | --- | --- |
| 今天 | 甲 | 暂停值日 |
| 明天 | 甲 | 甲 |
| 后天 | 乙 | 甲 |
| 再后一天 | 丙 | 乙 |

使用步骤：

1. 下滑到管理员入口，输入管理密码。
2. 点击“从今天起顺延一天”，查看未来七天的变化。
3. 确认无误后点击确认按钮。只看预览或取消，不会修改实际排班。

整体暂停不会给任何人增加欠班，也不会消耗已有轮空次数或补班天数。再次主动发起并确认操作，可以再顺延一天。

暂停日不会发送催促，已经发送的提醒不会撤回。该操作只允许管理员执行；请求重试不会重复顺延。

### 个人临时轮空

轮空不会删除舍友的值日责任，只会把责任暂时往后推。

- 标记 1 次：跳过下一次轮到自己的日期，之后连续值日 2 天。
- 标记 2 次：跳过两次轮换，之后连续值日 3 天。
- 标记 3 次：跳过三次轮换，之后连续值日 4 天。

轮空记录保存在 `duty_skips` 表中，网页和每日通知使用同一套排班算法。

这里的“次数”是跳过轮到自己的次数，不是离开宿舍的天数。首页选择舍友、开始日期和次数后提交即可；错误记录可以在管理员面板撤销。

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
- `pause_migration.sql`：新增 `duty_pauses` 表、完整排班读取函数和管理员顺延事务函数。
- `test_schedule.py`、`test_pauses.py`：轮空、顺延与模拟通知测试。
- `.github/workflows/clock.yml`：每日定时任务。

## 部署步骤

### 1. 准备数据库

已有轮空功能的项目，只需在 Supabase SQL Editor 中执行新增的 `pause_migration.sql`，不必重跑旧 `schema.sql`。暂停功能迁移可重复执行，不会立即创建真实暂停日，也不会删除原有排班数据。

首次部署需先准备 `dorm_rules` 表和宿舍记录，字段包括 `dorm_id`（唯一宿舍号）、`roommates`（英文逗号分隔的名单）、`anchor_date`（锚点日期）、`anchor_person`（当天负责人）和 `pushplus_topic`（推送群组）。随后依次执行 `schema.sql`、`pause_migration.sql`。这两份脚本不负责创建最初的 `dorm_rules` 表。

### 2. Supabase RLS

`dorm_rules` 至少需要允许 `anon` 和 `authenticated` 读取；`duty_skips` 的读取和新增策略已包含在 `schema.sql` 中。

不要给 `anon` 开放修改或删除已有轮空记录的权限。

暂停记录对访客只读；整体顺延通过服务器端 `service_role` 调用专用函数执行。暂停记录写入和未来轮空日期移动在同一事务内完成。

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

定时任务使用北京时间计算日期。工作流计划每天 UTC 23:05 运行，对应北京时间次日 07:05；GitHub Actions 可能延迟，不能保证准点送达。

### 5. 更新并部署代码

数据库迁移成功后，将 `app.py`、`notify.py`、`schedule.py` 一起提交到 GitHub 仓库根目录，等待 Streamlit 自动部署。已有项目无需新增 Secrets。

部署后先检查首页与管理员七天预览，确实需要当天暂停时再确认。若缺少迁移或无法读取完整排班，新版会显示错误并停止发送提醒，避免使用不完整的数据计算。

## 运行逻辑

网页和通知脚本通过同一个数据库读取函数，取得同一快照中的 `dorm_rules`、有效的 `duty_skips` 和 `duty_pauses`，再使用共享算法逐日计算。个人轮空会累计待补责任，因此之后连续值日天数等于轮空次数加 1；整体暂停则冻结当天的轮换状态，不消耗任何人的轮空或补班次数。浏览页面本身不会改变这些记录。

通知脚本在寒暑假期间仍尝试轻量数据库查询，但不发送提醒；普通周末照常提醒，法定节假日由 `chinesecalendar` 判断。当前寒假范围为 1 月 15 日至 2 月 20 日，暑假范围为 7 月 11 日至 8 月 29 日。这些假期规则只控制通知，不自动插入暂停日。

管理员设置的暂停日不发送催促；前一天的通知会显示“明天暂停值日”。已经发出的提醒不会撤回，也不会因顺延自动补发。

## 本地检查

```bash
python3 -m py_compile app.py notify.py schedule.py
python3 test_schedule.py
python3 -m unittest test_pauses -v
```

> 由 212 宿舍维护。少一点争论，多一点按时倒垃圾。
