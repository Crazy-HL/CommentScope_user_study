# 管理员后台设计：实验统计仪表盘

- **日期**：2026-09-13
- **状态**：待实施
- **关联项目**：CommentScope 实验系统

## 1. 背景与目标

当前实验系统已经把参与者实验过程写入 SQLite，包括文章区块、滚动与评论交互事件、逐题回答、主观评价、偏好和访谈资料。管理员后台的目标不是展示一张原始数据大表，而是让研究者登录后直接看到可用于实验监控和论文分析的统计结果。

第一版需要同时满足：

1. 通过固定账号密码保护管理员页面；
2. 展示实验进度和数据完整性，而不是只显示原始记录；
3. 统一由后端计算核心统计指标，避免前端和论文脚本产生不同统计口径；
4. 提供论文风格的条件比较图、数值表和简短结果分析；
5. 保留现有 JSON/CSV 导出和参与者重置能力；
6. 不影响参与者实验页面；
7. 不新增或依赖 `mode = pilot/formal` 的实验流程设计。上线前由研究者手动删除测试数据。

## 2. 已确认的范围

### 2.1 登录

- 管理员页面路径：`/admin`。
- 默认本地账号：`admin`。
- 默认本地密码：`admin123`。
- 账号和密码通过服务器环境变量覆盖：

```env
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
ADMIN_SESSION_SECRET=change-this-in-production
```

- 登录成功后使用 HttpOnly、SameSite=Lax 的会话 Cookie；密码不写入 URL、前端源码或统计数据。
- 统计、导出和重置接口均要求管理员会话。
- 为兼容现有部署，已有 `RESEARCHER_ADMIN_TOKEN` 的 Bearer 认证可以在迁移期间继续支持；新页面只使用账号密码登录得到的会话。
- 登出后清除会话 Cookie。

### 2.2 页面

管理员后台登录后提供两个用途不同的页面：

1. 普通总览页 `/admin`：用容易理解的进度卡片和条件摘要，快速查看实验是否正常进行；
2. 论文分析页 `/admin/analysis`：展示条件比较图、指标明细、结果分析文字和数据完整性检查。

两页共享管理员会话、后端统计口径、刷新、导出和参与者重置能力。两个页面均展示后端聚合结果。原始事件和逐题记录不作为主视图，只通过导出功能获取。

## 3. 统计口径

### 3.1 数据纳入规则

- 默认排除 `sessions.status = 'reset'` 的会话。
- 实验总览统计所有未重置会话，并分别显示 active、completed、reset 数量。
- 条件比较统计以 `article_sessions` 为基本分析行，即一个参与者完成一篇文章对应一个观察值。
- 指标只有在对应数据存在时才参与该指标的均值、中位数和置信区间计算；页面同时显示该指标的有效 `n`。
- 默认不把未完成的文章区块当作完整结果；若某个指标已保存，则可在数据完整性区域看到其部分数据，但论文分析图默认仅纳入文章区块完成且指标存在的观察值。
- 所有时间统一以毫秒存储，在页面显示为秒；统计 API 同时返回原始毫秒值和用于展示的秒值不需要重复存储，前端负责格式化。

### 3.2 实验规模与进度

预期正式实验规模固定为：

- 24 名参与者；
- 每人 4 篇文章；
- 96 个 participant-article session；
- 4 个条件：TE、CS、SE、BL；
- 每个文章 × 条件组合预期 6 个观察值；
- 逐题回答预期 960 条：CRA 384、ACA 192、CTI 192、LOCATION 192；
- 每个文章区块 1 份 workload survey，共 96；
- 偏好排序和访谈各预期 24 份。

这些是数据质量检查的预期值，不是限制数据库写入的硬编码规则。

### 3.3 核心与重要指标

对每个条件返回以下 descriptive statistics：`n`、mean、median、标准差、95% CI（能够计算时）以及原始 observation 数组或用于绘图的 participant-level 点。

核心结果：

- **CTIA**：每个文章区块 2 道 CTI 题的正确数 / 2；取值 0、0.5、1。
- **CTIRT**：每个文章区块两道 CTI 题 `elapsed_ms` 的平均值；以毫秒返回，页面以秒显示。

重要结果：

- **CRA**：每个文章区块四道 CRA 题的正确数 / 4。
- **ACA**：每个文章区块两道 ACA 题的正确数 / 2。
- **CLA**：每个文章区块两道 LOCATION 题的正确数 / 2。
- **CLT**：每个文章区块两道 LOCATION 题 `elapsed_ms` 的平均值。
- **Initial Reading Time**：`initial_reading_time_ms`。
- **NSD**：优先使用 `normalized_scroll_distance`；若旧记录缺少该字段，则由滚动事件回退计算，并在数据质量中标记为 fallback。
- **Comment Interaction Count**：`comment_interaction_count`，仅作为辅助行为指标。
- **RC / CA**：workload survey 中的 `reading_continuity`、`comment_accessibility`，取值 1–7。
- **NASA-TLX**：六个维度分别返回，主要强调 `mental_demand`、`effort`、`frustration`，其余三项作为补充，不计算未经两两比较加权的 NASA-TLX 总分。

辅助指标：

- `scroll_event_count`、`total_scroll_distance_px`、`max_scroll_y`；
- 文章级评论点击/打开/关闭/段落按钮次数；
- 偏好排名和 preferred condition；
- 访谈回答数量和是否缺失。访谈文本不在概览页全文展示，避免后台首页过长；本阶段只显示提交数量与完整性状态，并保留导出获取全文。

### 3.4 偏好统计

返回每个条件：

- 平均排名；
- 中位数排名；
- 排名为 1 的次数；
- 排名为 4 的次数；
- 有效排名人数。

同时返回 preferred condition 的频数和比例。偏好理由只显示已提交数量，全文通过导出获取。

### 3.5 结果分析文字

后端返回基于 descriptive statistics 的分析句子，前端按卡片展示。分析必须明确是“描述性结果”，不得在没有预设统计检验时宣称显著或因果结论。至少生成：

- CTIA 最高/最低条件及差值；
- CTIRT 最快/最慢条件及差值；
- CRA、ACA、CLA 的最高条件；
- 阅读时间、NSD、RC、CA 的条件差异提示；
- 有效样本量不足或数据完整性问题提示；
- 当前数据距离预期 24 人/96 区块的完成进度。

当有效数据不足以比较时，返回“当前有效数据不足，暂不进行条件比较”，而不是返回伪造的 0 或排名。

## 4. 后端 API 设计

### 4.1 认证接口

```http
POST /api/admin/login
Content-Type: application/json

{"username":"admin","password":"admin123"}
```

成功：HTTP 200，设置 HttpOnly 会话 Cookie，返回：

```json
{"authenticated":true,"username":"admin"}
```

失败：HTTP 401：

```json
{"error":"invalid_credentials"}
```

```http
GET /api/admin/me
POST /api/admin/logout
```

`/me` 返回当前会话状态；未登录返回 401。`/logout` 清除会话并返回 `{"logged_out": true}`。

### 4.2 统计接口

```http
GET /api/admin/summary
GET /api/admin/analysis
GET /api/admin/data-quality
```

三个接口都支持相同的可选查询参数：

```text
participant_id
article_id       A02/A03/A04/A07
condition        TE/CS/SE/BL
status           active/completed
```

参数只用于筛选返回统计，不改变数据库。

`/summary` 返回结构固定包含：

```json
{
  "scope": {"participant_id": null, "article_id": null, "condition": null, "status": null},
  "overview": {
    "expected_participants": 24,
    "participants_started": 0,
    "participants_completed": 0,
    "participants_active": 0,
    "article_sessions_expected": 96,
    "article_sessions_started": 0,
    "article_sessions_completed": 0,
    "responses": {"total": 0, "cra": 0, "aca": 0, "cti": 0, "location": 0},
    "surveys": 0,
    "preferences": 0,
    "interviews": 0
  },
  "conditions": {"TE": {}, "CS": {}, "SE": {}, "BL": {}},
  "metrics": {},
  "preference": {},
  "last_updated_at": null
}
```

`/analysis` 返回可直接展示的分析段落和逐项依据：

```json
{
  "generated_from": {"article_sessions": 0, "responses": 0, "surveys": 0},
  "statements": [
    {"metric":"CTIA","text":"当前有效数据不足，暂不进行条件比较。","severity":"info","evidence":{}}
  ]
}
```

`/data-quality` 返回问题列表，每项包括 `severity`（info/warning/error）、`code`、`message`、`count` 和可选的 affected identifiers。检查包括：

- 参与者/文章区块数量是否达到预期；
- 每个已完成文章区块是否有 4 CRA、2 ACA、2 CTI、2 LOCATION；
- 已完成文章区块是否缺少 workload；
- 偏好和访谈是否缺失；
- 是否存在异常条件、文章编号、重复活动会话；
- 是否有负值或明显异常的答题/阅读时长；
- normalized scroll distance 是否由 fallback 得到。

### 4.3 现有接口兼容

保留：

```http
GET /api/admin/export?format=json|csv
GET /api/admin/status
POST /api/admin/reset/<participant_id>
```

实现管理员会话保护；迁移期间继续接受已有 `Authorization: Bearer RESEARCHER_ADMIN_TOKEN`，以避免已有脚本和部署方式突然失效。导出内容不在首页全部渲染，仅提供下载按钮。

## 5. 前端设计

### 5.1 路由与隔离

当前项目未使用 Vue Router。第一版根据 `window.location.pathname` 在入口选择参与者应用或管理员应用：

- `/`：现有参与者实验流程；
- `/admin`：管理员登录/仪表盘。

管理员组件放在 `client/src/components/admin/`，管理员 API 封装独立于 participant API。参与者页面不显示管理员入口，也不携带管理员会话信息。

### 5.2 登录状态

- 首次打开 `/admin` 显示用户名和密码输入框；
- 登录成功后加载 summary、analysis、data-quality；
- Cookie 由浏览器自动携带，前端不读取密码；
- 刷新页面调用 `/api/admin/me` 恢复登录状态；
- 401 时返回登录界面并清除本地页面状态；
- 页面提供登出按钮。

### 5.3 仪表盘布局

顶部：

- 标题“CommentScope 管理员后台”；
- 最近更新时间；
- 刷新按钮；
- 登出按钮。

第一行总览卡片：

- 已开始参与者 / 24；
- 已完成参与者；
- 已完成文章区块 / 96；
- 已收集逐题回答 / 960；
- 主观评价 / 96；
- 偏好 / 24；访谈 / 24。

筛选区：

- 参与者、文章、条件、会话状态下拉框；
- 应用筛选和清除筛选；
- 筛选变化后重新请求后端统计接口。

论文分析区：

- 核心指标 CTIA、CTIRT 放在最前；
- 任务指标和阅读/主观指标分组；
- 每个图旁边显示 n、均值/中位数、95% CI；
- 使用论文风格的 SVG/CSS 图，不引入必须联网的图表依赖；
- 采用白底、细黑轴、灰色虚线网格、条件色带、参与者级散点、均值或中位数标记。

操作区：

- JSON/CSV 导出按钮；
- 参与者重置按钮放在危险操作区域，必须输入参与者编号并二次确认；
- 重置后刷新所有统计，并明确显示“该参与者的活动会话已重置”。

响应式要求：桌面端优先，窄屏下图表允许横向滚动，统计卡片改为单列；不能影响参与者实验的既有布局。

## 6. 错误与安全要求

- 未登录访问任何 `/api/admin/*` 统计、导出、状态和重置接口都返回 401 JSON；
- 登录失败不区分“账号不存在”还是“密码错误”；
- 不在日志或错误响应中输出密码；
- 会话 Cookie 使用 HttpOnly、SameSite=Lax；生产环境在 HTTPS 下启用 Secure；
- 默认 `admin123` 只为当前本地测试便利，部署到公网前必须通过环境变量替换；
- 所有统计 SQL 使用参数绑定，不拼接用户输入；
- 空数据库和部分数据必须能正常返回 200，不能因除零或空数组导致 500；
- 统计失败时前端显示错误提示，不覆盖已有成功数据。

## 7. 测试验收标准

后端：

1. 正确账号密码登录成功并设置会话；
2. 错误账号密码返回 401；
3. 未登录不能访问 summary、analysis、data-quality、export、reset；
4. 登录后能访问所有管理员接口；
5. summary 能正确聚合空数据库和带样例数据的四种条件；
6. CTIA/CTIRT、CRA/ACA/CLA/CLT 的 n、均值、中位数和有效范围正确；
7. workload、偏好、访谈缺失能被 data-quality 标记；
8. 筛选参数只影响统计结果，不影响数据库；
9. 保留现有导出格式和 Bearer token 兼容行为；
10. 重置功能仍然受保护且不破坏参与者 API。

前端：

1. `/` 仍进入参与者实验页面；
2. `/admin` 显示登录页；
3. 登录后显示总览、筛选器、核心指标和分析文字；
4. 401 时回到登录页；
5. 空数据、部分数据、接口错误都有可读提示；
6. 导出按钮能触发下载；
7. 重置按钮需要二次确认；
8. 生产构建成功，现有实验流程测试继续通过。

## 8. 非目标

本阶段不做：

- 多管理员账号、角色权限和账号管理；
- 在线编辑实验材料或题目；
- 将访谈文本自动编码成研究主题；
- 正式推断统计、混合效应模型、p 值或效应量报告；
- 在数据库中新增 pilot/formal 工作流；
- 在后台首页显示全部原始事件明细；
- 重构参与者端文章评论展示。
