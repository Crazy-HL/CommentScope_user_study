# 管理员后台 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 CommentScope 实验系统增加一个受账号密码保护的 `/admin` 单页统计仪表盘，由后端统一计算实验进度、论文指标、结果分析和数据完整性，并保留现有导出与参与者重置能力。

**Architecture:** 在 Tornado 后端新增管理员认证与统计服务层；`/api/admin/summary`、`/api/admin/analysis` 和 `/api/admin/data-quality` 使用同一套 SQLite 查询和聚合逻辑。Vue 入口根据路径把 `/admin` 与参与者端隔离，管理员端通过独立 API 客户端登录并展示 CSS/SVG 论文风格图，不引入必须联网的图表依赖。

**Tech Stack:** Python 3、Tornado、SQLite、pytest；Vue 3、Vue CLI、axios、原生 CSS/SVG。

## Global Constraints

- 管理员页面路径固定为 `/admin`，参与者页面 `/` 的现有流程和评论展示不得改变。
- 默认管理员账号密码为 `admin / admin123`，但必须允许 `ADMIN_USERNAME`、`ADMIN_PASSWORD`、`ADMIN_SESSION_SECRET` 环境变量覆盖。
- 密码不得写入前端源码、URL、统计响应或日志；登录使用 HttpOnly、SameSite=Lax 会话 Cookie。
- 现有 `RESEARCHER_ADMIN_TOKEN` Bearer 认证在迁移期间继续兼容，不能破坏已有导出、状态和重置脚本。
- 默认统计排除 `sessions.status = 'reset'` 的会话；文章区块是条件比较的基本观察单位。
- 主要指标为 CTIA、CTIRT；重要指标为 CRA、ACA、CLA、CLT、Initial Reading Time、NSD、RC、CA；NASA-TLX 六维度分别保留，不计算未经标准加权程序的总分。
- 空数据库、部分数据、筛选后无数据和统计异常必须返回可读结果，不得因为除零或空数组返回 HTTP 500。
- 不新增 `mode = pilot/formal` 工作流，不重构参与者端文章与评论嵌入方式。
- 当前仓库已有大量未提交改动和未跟踪文件；只修改本计划列出的管理员相关文件，不执行 `git reset --hard` 或 `git clean -fd`。

## 文件边界与职责

| 文件 | 职责 |
|---|---|
| `server/admin_auth.py` | 管理员凭据读取、会话 Cookie 签发/校验、登录/登出辅助函数 |
| `server/admin_stats.py` | 从 SQLite 读取筛选数据，计算 summary、analysis、data-quality JSON |
| `server/server.py` | 注册登录、会话、统计、兼容认证的 Tornado handlers |
| `server/database.py` | 只在需要时增加管理员聚合查询辅助方法；不改变现有参与者写入语义 |
| `server/tests/test_admin_auth.py` | 认证单元测试 |
| `server/tests/test_admin_stats.py` | 统计和完整性聚合测试 |
| `server/tests/test_api.py` | 管理员 HTTP 契约测试扩展 |
| `client/src/admin/adminApi.js` | 管理员 API 请求、登录和登出封装 |
| `client/src/components/admin/AdminLogin.vue` | 登录表单 |
| `client/src/components/admin/AdminDashboard.vue` | 单页仪表盘、筛选、刷新、导出、重置交互 |
| `client/src/components/admin/AdminMetricChart.vue` | 无第三方依赖的条件比较图 |
| `client/src/components/admin/admin.css` | 管理员页面独立样式 |
| `client/src/App.vue` | 按 URL 路径隔离 `/admin` 与参与者端 |
| `client/tests/admin-dashboard.test.cjs` | 管理员前端 API/渲染契约检查 |
| `.env.example` | 增加管理员账号、密码和会话密钥配置说明 |
| `README_EXPERIMENT.md` | 增加本地和服务器启动管理员后台说明 |

---

### Task 1: 建立管理员认证契约和会话后端

**Files:**
- Create: `/Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue/server/admin_auth.py`
- Modify: `/Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue/server/server.py`
- Create: `/Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue/server/tests/test_admin_auth.py`
- Modify: `/Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue/server/tests/test_api.py`
- Modify: `/Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue/.env.example`

**Interfaces:**
- Produces `AdminAuth` with `credentials()`, `verify_credentials(username, password)`, `set_session(handler, username)`, `clear_session(handler)`, and `is_authenticated(handler)`.
- Produces handlers `AdminLoginHandler`, `AdminMeHandler`, `AdminLogoutHandler`.
- Existing Bearer-token `AdminHandler.check_auth()` remains available for compatibility; new admin handlers accept either a valid session cookie or the existing Bearer token.

- [ ] **Step 1: Write failing unit tests for credential and session behavior**

Add tests that assert:

```python
from admin_auth import AdminAuth


def test_default_credentials_are_admin_admin123(monkeypatch):
    monkeypatch.delenv("ADMIN_USERNAME", raising=False)
    monkeypatch.delenv("ADMIN_PASSWORD", raising=False)
    auth = AdminAuth()
    assert auth.credentials() == ("admin", "admin123")


def test_environment_credentials_override_defaults(monkeypatch):
    monkeypatch.setenv("ADMIN_USERNAME", "researcher")
    monkeypatch.setenv("ADMIN_PASSWORD", "strong-test-password")
    assert AdminAuth().credentials() == ("researcher", "strong-test-password")


def test_password_comparison_is_false_for_wrong_password(monkeypatch):
    monkeypatch.setenv("ADMIN_USERNAME", "admin")
    monkeypatch.setenv("ADMIN_PASSWORD", "admin123")
    auth = AdminAuth()
    assert auth.verify_credentials("admin", "wrong") is False
    assert auth.verify_credentials("other", "admin123") is False
    assert auth.verify_credentials("admin", "admin123") is True
```

Add HTTP tests that post `/api/admin/login` with valid and invalid credentials, then call `/api/admin/me` with the returned cookie, and finally `/api/admin/logout`. Verify that an unauthenticated `/api/admin/me` returns 401 and that the response never contains the password.

- [ ] **Step 2: Run the focused tests and verify they fail**

Run:

```bash
cd /Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue
python3 -m pytest server/tests/test_admin_auth.py server/tests/test_api.py -q
```

Expected: FAIL because the auth module and login/me/logout handlers do not exist.

- [ ] **Step 3: Implement environment-based credentials and signed session cookie**

Implement `AdminAuth` using `hmac.compare_digest` for username/password comparisons. Use Tornado's signed-cookie support with a secret from `ADMIN_SESSION_SECRET`, falling back only for local development to a deterministic development secret. Set a cookie named `comment_scope_admin_session` with:

```python
handler.set_secure_cookie(
    "comment_scope_admin_session",
    username,
    httponly=True,
    samesite="lax",
    secure=os.environ.get("ADMIN_COOKIE_SECURE", "0") == "1",
    max_age_days=1,
)
```

Configure Tornado application `cookie_secret` from `ADMIN_SESSION_SECRET` and reject empty/invalid sessions. Do not store the password in the cookie.

- [ ] **Step 4: Implement handlers and preserve Bearer compatibility**

Add:

```python
class AdminLoginHandler(JsonHandler):
    def post(self):
        data = self.body_json()
        if self.auth.verify_credentials(str(data.get("username", "")), str(data.get("password", ""))):
            self.auth.set_session(self, self.auth.credentials()[0])
            self.respond({"authenticated": True, "username": self.auth.credentials()[0]})
        else:
            self.respond({"error": "invalid_credentials"}, 401)
```

`AdminMeHandler` returns `{ "authenticated": true, "username": "admin" }` only when authenticated; otherwise 401. `AdminLogoutHandler` clears the cookie and returns `{ "logged_out": true }`. Refactor `AdminHandler.check_auth()` to first accept a valid cookie, then fall back to `Authorization: Bearer <RESEARCHER_ADMIN_TOKEN>`.

Register the handlers before the existing admin export/status/reset routes. Pass one `AdminAuth` instance into the app so every request uses the same secret configuration.

- [ ] **Step 5: Run auth and regression tests**

Run:

```bash
python3 -m pytest server/tests/test_admin_auth.py server/tests/test_api.py -q
```

Expected: all focused tests pass, including existing Bearer-token export/reset tests.

- [ ] **Step 6: Commit only the authentication files**

```bash
git add server/admin_auth.py server/server.py server/tests/test_admin_auth.py server/tests/test_api.py .env.example
git commit -m "feat: add administrator session authentication"
```

Do not stage unrelated existing changes.

---

### Task 2: Implement backend statistical aggregation

**Files:**
- Create: `/Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue/server/admin_stats.py`
- Create: `/Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue/server/tests/test_admin_stats.py`
- Modify: `/Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue/server/server.py`

**Interfaces:**
- Produces `AdminStats(db).summary(filters)`, `AdminStats(db).analysis(filters)`, and `AdminStats(db).data_quality(filters)`.
- `filters` is a dictionary containing optional `participant_id`, `article_id`, `condition`, and `status` strings.
- Each metric result has `n`, `mean`, `median`, `stddev`, `ci95`, and `observations`; empty metrics return `n: 0`, numeric values `None`, and `observations: []`.
- Produces handlers `AdminSummaryHandler`, `AdminAnalysisHandler`, and `AdminDataQualityHandler` at `/api/admin/summary`, `/api/admin/analysis`, and `/api/admin/data-quality`.

- [ ] **Step 1: Write failing aggregation tests with deterministic SQLite fixtures**

Use `ExperimentDatabase` with a temporary SQLite path. Insert two completed article sessions in each of TE and CS, responses for all four task types, workload rows, preference rows, and one interview. Assert:

```python
def test_ctia_and_ctirt_are_aggregated_per_article_session(db_with_fixture):
    result = AdminStats(db_with_fixture).summary({})
    assert result["metrics"]["CTIA"]["TE"]["n"] == 2
    assert result["metrics"]["CTIA"]["TE"]["mean"] == 0.75
    assert result["metrics"]["CTIRT"]["TE"]["mean"] == 1500.0
```

Also test CRA (4 items), ACA (2), CLA (2), CLT (2), initial reading time, normalized scroll distance, RC, CA, and all six NASA-TLX dimensions. Test that a `status=completed` filter excludes active rows and that `condition=CS` returns only CS observations. Test empty databases return 200-compatible JSON with `n == 0` and `None` means.

- [ ] **Step 2: Run the focused stats tests and verify they fail**

Run:

```bash
python3 -m pytest server/tests/test_admin_stats.py -q
```

Expected: FAIL because `admin_stats.py` and `AdminStats` do not exist.

- [ ] **Step 3: Implement safe filter construction**

Create a single private query helper that builds conditions only from a fixed allow-list:

```python
ALLOWED_FILTERS = {
    "participant_id": "s.participant_id",
    "article_id": "a.article_id",
    "condition": "a.condition",
    "status": "a.status",
}
```

For every non-empty filter, append `column = ?` and bind the value. Always join `sessions s` to `article_sessions a`, exclude reset sessions by default, and never interpolate raw query parameter names or values.

- [ ] **Step 4: Implement metric helpers**

Implement:

```python
def metric_summary(values):
    values = [float(value) for value in values if value is not None]
    if not values:
        return {"n": 0, "mean": None, "median": None, "stddev": None, "ci95": None, "observations": []}
    mean = sum(values) / len(values)
    median = statistics.median(values)
    stddev = statistics.stdev(values) if len(values) > 1 else 0.0
    ci95 = 1.96 * stddev / math.sqrt(len(values)) if len(values) > 1 else 0.0
    return {"n": len(values), "mean": mean, "median": median, "stddev": stddev, "ci95": ci95, "observations": values}
```

Use descriptive 95% CI only; do not implement p-values or inferential claims in this task.

- [ ] **Step 5: Implement article-session task aggregation**

For each selected article session, aggregate responses grouped by `(session_id, article_order)`:

```python
CRA = sum(correct for question_type == "cra") / 4
ACA = sum(correct for question_type == "aca") / 2
CTIA = sum(correct for question_type == "cti") / 2
CTIRT = mean(elapsed_ms for question_type == "cti")
CLA = sum(correct for question_type == "location") / 2
CLT = mean(elapsed_ms for question_type == "location")
```

Only emit a complete task metric when the required number of responses exists. Use `a.initial_reading_time_ms`, `a.normalized_scroll_distance`, `a.comment_interaction_count`, and the workload table for article-level metrics. Return metrics grouped by condition in stable order `TE`, `CS`, `SE`, `BL`.

- [ ] **Step 6: Implement overview, preferences, and response counts**

Return expected counts 24/96/960/96/24/24 alongside observed counts. Count participants from non-reset sessions, completed participants from `sessions.status = 'completed'`, and article-session started/completed from the selected scope. Count response rows by normalized question type aliases (`cra`, `aca`, `cti`, `location`). Preference statistics must include average/median rank, rank-one count, rank-four count, and preferred-condition frequency.

- [ ] **Step 7: Add admin stats handlers and query parsing**

Parse only the four documented query parameters, trim values, and return HTTP 400 for unknown condition/article/status values. Handler behavior:

```python
class AdminSummaryHandler(AdminHandler):
    def get(self):
        if not self.check_auth():
            return
        self.respond(AdminStats(self.db).summary(self.admin_filters()))
```

Use the same auth path as existing admin endpoints.

- [ ] **Step 8: Run backend aggregation tests**

Run:

```bash
python3 -m pytest server/tests/test_admin_stats.py server/tests/test_api.py -q
```

Expected: all aggregation, filtering, auth, export, reset, and existing participant tests pass.

- [ ] **Step 9: Commit only the statistics files**

```bash
git add server/admin_stats.py server/server.py server/tests/test_admin_stats.py server/tests/test_api.py
git commit -m "feat: add administrator experiment statistics APIs"
```

---

### Task 3: Implement result analysis and data-quality reports

**Files:**
- Modify: `/Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue/server/admin_stats.py`
- Modify: `/Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue/server/tests/test_admin_stats.py`
- Modify: `/Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue/server/server.py`

**Interfaces:**
- `AdminStats.analysis(filters)` returns `generated_from` counts and `statements` with `metric`, `text`, `severity`, and `evidence`.
- `AdminStats.data_quality(filters)` returns `expected`, `observed`, and `issues`; each issue has `severity`, `code`, `message`, `count`, and optional `affected` list.

- [ ] **Step 1: Write failing analysis and quality tests**

Assert that:

```python
def test_analysis_is_descriptive_and_names_highest_ctia_condition(db_with_fixture):
    result = AdminStats(db_with_fixture).analysis({})
    statement = next(item for item in result["statements"] if item["metric"] == "CTIA")
    assert "CTIA" in statement["text"]
    assert statement["evidence"]["highest_condition"] == "TE"
    assert "显著" not in statement["text"]
```

Assert data quality identifies missing CRA/ACA/CTI/LOCATION responses, missing workload rows, missing preference/interview rows, incomplete expected counts, invalid conditions, negative durations, and fallback NSD calculations. Assert an empty database returns warnings rather than raising.

- [ ] **Step 2: Run tests and verify the new assertions fail**

Run:

```bash
python3 -m pytest server/tests/test_admin_stats.py -q
```

Expected: FAIL because analysis statements and quality issue generation are not implemented.

- [ ] **Step 3: Implement conservative descriptive analysis**

Add helpers that choose highest/lowest conditions only when at least one valid metric has `n > 0`. Text must say “描述性结果” or equivalent and report n and difference. If fewer than two conditions have data, return an informational insufficient-data statement. Do not mention significance, causality, p-values, or “improves”.

- [ ] **Step 4: Implement data-quality checks**

Use the same filtered article-session set and inspect:

1. observed participant/article-session/response/survey/preference/interview counts versus expected;
2. every completed article session has exactly 4 CRA, 2 ACA, 2 CTI, and 2 LOCATION responses;
3. workload exists for every completed article session;
4. preference/interview records exist for completed participants;
5. condition/article values belong to the fixed experiment configuration;
6. elapsed and reading times are non-negative and bounded by a clearly named warning threshold;
7. `normalized_scroll_distance` missing while scroll events exist is marked `nsd_fallback`.

Do not reject or delete data from this report.

- [ ] **Step 5: Run backend tests**

```bash
python3 -m pytest server/tests/test_admin_stats.py server/tests/test_api.py -q
```

Expected: all tests pass.

- [ ] **Step 6: Commit analysis and data-quality implementation**

```bash
git add server/admin_stats.py server/server.py server/tests/test_admin_stats.py
 git commit -m "feat: add administrator analysis and data quality reports"
```

---

### Task 4: Add the isolated Vue administrator application shell and login

**Files:**
- Create: `/Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue/client/src/admin/adminApi.js`
- Create: `/Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue/client/src/components/admin/AdminLogin.vue`
- Create: `/Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue/client/src/components/admin/AdminDashboard.vue`
- Create: `/Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue/client/src/components/admin/AdminMetricChart.vue`
- Create: `/Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue/client/src/components/admin/admin.css`
- Modify: `/Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue/client/src/App.vue`
- Create: `/Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue/client/tests/admin-dashboard.test.cjs`

**Interfaces:**
- `adminApi` exports `login`, `me`, `logout`, `summary`, `analysis`, `dataQuality`, `exportUrl`, and `resetParticipant`.
- All axios requests use `withCredentials: true`, the same `/api` base URL, and do not put credentials in query strings.
- `AdminLogin` emits `authenticated` with the returned username; `AdminDashboard` loads all three admin APIs and emits `logout`.
- `App.vue` renders the admin shell only when `window.location.pathname === '/admin'`; all participant computed state and stage components remain unchanged for `/`.

- [ ] **Step 1: Write failing frontend contract tests**

Create a Node test that reads source files and asserts:

```js
assert.match(app, /window\.location\.pathname/);
assert.match(app, /AdminLogin/);
assert.match(api, /withCredentials:\s*true/);
assert.match(api, /\/api\/admin\/login/);
assert.match(login, /username/);
assert.match(login, /password/);
assert.match(dashboard, /summary/);
assert.match(dashboard, /data-quality/);
```

Also assert participant components still occur in `App.vue` and `/admin` is not sent as a participant ID or experiment mode.

- [ ] **Step 2: Run the frontend test and verify it fails**

Run:

```bash
cd /Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue/client
node tests/admin-dashboard.test.cjs
```

Expected: FAIL because the admin source files and path split do not exist.

- [ ] **Step 3: Implement the admin API client**

Create an axios client:

```js
import axios from "axios";

const http = axios.create({
  baseURL: process.env.VUE_APP_API_BASE_URL || "/api",
  timeout: 15000,
  withCredentials: true,
});

const query = filters => Object.fromEntries(
  Object.entries(filters || {}).filter(([, value]) => value)
);

export default {
  login(username, password) { return http.post("/admin/login", { username, password }); },
  me() { return http.get("/admin/me"); },
  logout() { return http.post("/admin/logout"); },
  summary(filters) { return http.get("/admin/summary", { params: query(filters) }); },
  analysis(filters) { return http.get("/admin/analysis", { params: query(filters) }); },
  dataQuality(filters) { return http.get("/admin/data-quality", { params: query(filters) }); },
  exportUrl(format = "csv") { return `/api/admin/export?format=${encodeURIComponent(format)}`; },
  resetParticipant(participantId) { return http.post(`/admin/reset/${encodeURIComponent(participantId)}`, {}); },
};
```

- [ ] **Step 4: Implement login page and path isolation**

`AdminLogin.vue` contains username/password fields, submit button, loading state, and a generic invalid-credentials/error message. Do not persist the password in localStorage or sessionStorage. Update `App.vue` with a top-level path branch that renders an `AdminLogin`/`AdminDashboard` state machine for `/admin`; the existing participant `onMounted`, session store, stages, and completion logic remain in the non-admin branch.

- [ ] **Step 5: Implement dashboard data loading shell**

`AdminDashboard.vue` must:

- call `summary`, `analysis`, and `dataQuality` on mount and when filters change;
- handle 401 by emitting logout or returning to login;
- show loading, error, and empty-data states;
- show cards for overview counts;
- include filters for participant, article, condition, and status;
- provide refresh and logout controls;
- provide CSV/JSON download links that preserve the existing Bearer-token compatibility limitation for now; if browser download cannot send the session cookie, replace the anchor with an authenticated blob download in this task rather than exposing a token in the URL.

- [ ] **Step 6: Run frontend contract test and production build**

```bash
node tests/admin-dashboard.test.cjs
npm run build
```

Expected: contract test passes and Vue production build succeeds.

- [ ] **Step 7: Commit only the admin shell files**

```bash
git add client/src/App.vue client/src/admin client/src/components/admin client/tests/admin-dashboard.test.cjs
 git commit -m "feat: add administrator dashboard shell"
```

---

### Task 5: Implement论文风格图表、结果说明和操作区

**Files:**
- Modify: `/Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue/client/src/components/admin/AdminDashboard.vue`
- Modify: `/Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue/client/src/components/admin/AdminMetricChart.vue`
- Modify: `/Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue/client/src/components/admin/admin.css`
- Modify: `/Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue/client/tests/admin-dashboard.test.cjs`

**Interfaces:**
- `AdminMetricChart` receives `title`, `metric`, `series`, `format`, and `higherIsBetter` props and renders condition rows with observations, center marker, and CI/error range.
- Dashboard receives the exact summary/analysis/data-quality payloads from Task 4 and does not recalculate core statistics in the browser.

- [ ] **Step 1: Extend failing frontend assertions**

Assert the dashboard source contains the required labels and actions:

```js
for (const label of ["CTIA", "CTIRT", "CRA", "ACA", "CLA", "CLT", "Reading Continuity", "Comment Accessibility", "NASA-TLX", "数据完整性", "导出", "重置参与者"]) {
  assert.match(dashboard, new RegExp(label));
}
assert.match(chart, /observations/);
assert.match(chart, /ci95/);
```

- [ ] **Step 2: Run the test and verify it fails**

```bash
node tests/admin-dashboard.test.cjs
```

Expected: FAIL for missing chart and dashboard sections.

- [ ] **Step 3: Implement the chart component with native SVG/CSS**

Render one horizontal comparison chart per metric:

- fixed condition order `TE`, `CS`, `SE`, `BL`;
- grey dashed grid;
- participant observations as small dots;
- mean marker for time/scale metrics and median marker where the payload specifies it;
- 95% CI line when `ci95` is not null;
- no chart when `n == 0`, with “暂无有效数据”;
- accessible labels and a compact table below each chart for exact n/mean/median.

Do not add ECharts, Chart.js, D3, or a remote script. Use inline SVG so the page works on the private server without external network access.

- [ ] **Step 4: Implement dashboard sections and result analysis**

Render:

1. overview cards;
2. filter bar;
3. “核心结果” CTIA and CTIRT first;
4. task profile CRA/ACA/CLA/CLT;
5. reading behavior and interaction metrics;
6. RC/CA and six NASA-TLX dimensions;
7. preference ranking summary;
8. analysis statements with severity styling;
9. data-quality issue list;
10. export controls and dangerous reset panel.

Use analysis API text verbatim as descriptive commentary; do not synthesize new significance claims in Vue.

- [ ] **Step 5: Implement authenticated download and reset confirmation**

Add an API method that requests `/admin/export?format=csv|json` with `withCredentials`, creates a Blob URL from the response, clicks a temporary download anchor, and revokes the URL. Reset must require typing/selecting a participant and calling `window.confirm` before POST; after success reload all dashboard payloads.

- [ ] **Step 6: Add responsive academic styling**

Use white cards, dark text, thin black axes, grey grid lines, muted teal/blue/coral condition accents, generous spacing, and CSS media queries. Keep charts readable on desktop; on narrow widths use horizontal overflow for chart panels rather than shrinking text below 11px.

- [ ] **Step 7: Run frontend tests and build**

```bash
node tests/admin-dashboard.test.cjs
npm run build
```

Expected: all frontend contract checks pass and build succeeds.

- [ ] **Step 8: Commit chart and dashboard features**

```bash
git add client/src/components/admin client/tests/admin-dashboard.test.cjs
 git commit -m "feat: add administrator analysis dashboard"
```

---

### Task 6: Documentation, full verification, and local launch

**Files:**
- Modify: `/Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue/.env.example`
- Modify: `/Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue/README_EXPERIMENT.md`
- Modify: `/Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue/server/tests/test_api.py`
- Modify: `/Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue/client/tests/admin-dashboard.test.cjs`

- [ ] **Step 1: Add deployment documentation**

Document:

```env
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
ADMIN_SESSION_SECRET=replace-with-a-long-random-value
ADMIN_COOKIE_SECURE=1
```

Document local URLs:

```text
参与者端：http://127.0.0.1:8888/
管理员端：http://127.0.0.1:8888/admin
```

Explain that the database is SQLite on the server disk, that data survives browser refresh/restart while the server and disk remain available, and that the researcher should back up/delete test data before formal launch.

- [ ] **Step 2: Run the complete backend suite**

```bash
cd /Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue
python3 -m pytest server/tests -q
```

Expected: all existing and new tests pass.

- [ ] **Step 3: Run all frontend checks and production build**

```bash
cd /Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue/client
npm run test:experiment
node tests/admin-dashboard.test.cjs
npm run build
```

Expected: experiment flow checks, admin dashboard checks, and production build all pass.

- [ ] **Step 4: Run a local smoke test with the real server**

Start the server with:

```bash
cd /Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue
ADMIN_USERNAME=admin ADMIN_PASSWORD=admin123 ADMIN_SESSION_SECRET=local-admin-secret PORT=8888 python3 server/server.py
```

Verify with a separate shell:

```bash
curl -i http://127.0.0.1:8888/admin
curl -i -c /tmp/commentscope-admin.cookies -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin123"}' \
  http://127.0.0.1:8888/api/admin/login
curl -i -b /tmp/commentscope-admin.cookies http://127.0.0.1:8888/api/admin/summary
curl -i -b /tmp/commentscope-admin.cookies http://127.0.0.1:8888/api/admin/analysis
curl -i -b /tmp/commentscope-admin.cookies http://127.0.0.1:8888/api/admin/data-quality
```

Expected: `/admin` serves the SPA, login returns 200 and a session cookie, all three statistics APIs return 200 JSON, and the participant page remains available at `/`.

- [ ] **Step 5: Inspect git diff and avoid unrelated changes**

```bash
git status --short
 git diff --check
```

Confirm only the listed admin files, documentation, and tests were modified by the implementation. Do not remove or reset the prior experiment-system changes.

- [ ] **Step 6: Commit documentation and final verification changes**

```bash
git add .env.example README_EXPERIMENT.md server/tests/test_api.py client/tests/admin-dashboard.test.cjs
 git commit -m "docs: document administrator dashboard deployment"
```

## Self-review checklist

- [ ] Every design requirement in `docs/superpowers/specs/2026-09-13-admin-dashboard-design.md` maps to at least one task.
- [ ] No task changes the participant article/comment rendering.
- [ ] No task adds a pilot/formal workflow.
- [ ] Statistics are calculated in the backend and include empty/partial data behavior.
- [ ] Existing Bearer token export/status/reset behavior remains compatible.
- [ ] Password is never persisted in browser storage or included in URLs.
- [ ] Admin route and participant route are isolated.
- [ ] Full backend tests, frontend tests, production build, and real-server smoke test are specified.
