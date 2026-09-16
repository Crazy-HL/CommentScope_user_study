# CommentScope 实验系统（方案 A）

这是一个 Vue 3 + Tornado + SQLite 的单体实验系统。参与者只需在首页选择研究者分配的 `P01`–`P24` 编号，系统会从服务端固定配置中加载文章顺序、评论展示条件和题目。

## 实验流程

每篇文章依次执行：自然阅读 → CRA（4题）→ ACA（2题）→ CTIA（2题）→ 评论定位（2题）→ NASA-TLX + RC + CA；4篇文章完成后填写界面偏好排序和4道必填访谈题。

参与者端不会返回正确答案、研究者锚点、组别或条件名称。答题和操作事件在每次请求时直接写入 SQLite，浏览器刷新或中断后可以从最后一个已保存阶段继续。

## 本地运行

### 1. 后端

```bash
cd /Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue
python3 -m venv .venv
. .venv/bin/activate
pip install tornado pytest
export EXPERIMENT_DB_PATH="$PWD/server/data/experiment.sqlite3"
export ADMIN_USERNAME=admin
export ADMIN_PASSWORD=admin123
export ADMIN_SESSION_SECRET='local-admin-session-secret'
python3 server/server.py
```

管理员后台地址：<http://127.0.0.1:8888/admin>

本地默认管理员账号为 `admin`，密码为 `admin123`。正式部署到自己的服务器前，请通过环境变量设置新的管理员密码和足够长的会话密钥；密码不会写入前端代码或统计接口响应。

### 2. 前端开发

另开终端：

```bash
cd /Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue/client
npm install
npm run serve
```

开发服务器会把 `/api` 代理到 `http://127.0.0.1:8888`。正式部署应使用生产构建：

```bash
npm run build
```

然后设置 `CLIENT_DIST_PATH` 指向生成的 `client/dist`，由 Tornado 直接提供静态页面；或使用 Nginx 提供 `dist`，将 `/api/` 反向代理到 Tornado。

## 管理员后台

访问 `/admin` 后使用管理员账号密码登录。登录后可在两个页面之间切换：普通总览页 `/admin` 用于快速查看实验进度和条件摘要，论文分析页 `/admin/analysis` 用于查看论文风格统计图、指标明细、描述性分析和数据质量；两页都由后端从 SQLite 计算统计结果。后台展示：

- 实验总览：参与者、文章区块、逐题回答、主观评价、偏好和访谈进度；
- CTIA、CTIRT 核心结果，以及 CRA、ACA、CLA、CLT；
- Initial Reading Time、NSD、滚动事件、总滚动距离和评论交互次数；
- RC、CA 和 NASA-TLX 六个维度；
- 按参与者、文章、条件和文章区块状态筛选；
- 描述性论文分析文字和数据完整性检查；
- 分析型 JSON/CSV 导出，以及逐条原始交互事件 JSON/CSV 导出；
- 参与者活动会话重置。

论文分析页只做描述性比较，不自动宣称统计显著性、因果关系或未经标准两两比较加权的 NASA-TLX 总分。

## 上线前检查

```bash
cd /Users/hl/Desktop/Comments_Annotations/TC_Enhancement-main/wikitable-vue
python3 server/scripts/import_materials.py
python3 server/scripts/preflight.py --db server/data/experiment.sqlite3 --require-admin-token
python3 -m pytest -q server/tests
cd client && npm run test:experiment && node tests/admin-dashboard.test.cjs && npm run build
```

上线前先在本地完整走一遍 P01–P24 分配、四种评论展示、刷新恢复、另一个浏览器占用提示、所有题目提交、管理员统计、导出和重置。正式实验开始前，按你的安排删除服务器 SQLite 中的预测试数据，并确认管理员后台的各项计数归零。

## 研究者数据操作

管理员网页登录使用 Cookie 会话。已有脚本仍可使用环境变量 `RESEARCHER_ADMIN_TOKEN` 进行兼容认证：

导出数据 CSV：

```bash
curl -H "Authorization: Bearer $RESEARCHER_ADMIN_TOKEN" \
  'http://127.0.0.1:8888/api/admin/export?format=csv' \
  -o experiment.csv
```

导出 JSON：

```bash
curl -H "Authorization: Bearer $RESEARCHER_ADMIN_TOKEN" \
  'http://127.0.0.1:8888/api/admin/export?format=json' \
  -o experiment.json
```

导出逐条原始事件 CSV/JSON（每条滚动、点击、评论操作、焦点变化和答题阶段事件一行）：

```bash
curl -H "Authorization: Bearer $RESEARCHER_ADMIN_TOKEN" \
  'http://127.0.0.1:8888/api/admin/export?dataset=events&format=csv' \
  -o experiment-events.csv

curl -H "Authorization: Bearer $RESEARCHER_ADMIN_TOKEN" \
  'http://127.0.0.1:8888/api/admin/export?dataset=events&format=json' \
  -o experiment-events.json
```

查看状态：

```bash
curl -H "Authorization: Bearer $RESEARCHER_ADMIN_TOKEN" \
  http://127.0.0.1:8888/api/admin/status
```

重置一个参与者（用于重新实验；历史记录会保留为 `reset`，不会混入默认统计）：

```bash
curl -X POST -H "Authorization: Bearer $RESEARCHER_ADMIN_TOKEN" \
  http://127.0.0.1:8888/api/admin/reset/P01
```

## SQLite 持久化与备份

只要 `EXPERIMENT_DB_PATH` 指向服务器上的持久磁盘，SQLite 数据不会因浏览器关闭或 Tornado 重启而消失。SQLite WAL 模式下建议使用在线备份 API，不要在实验进行时直接复制数据库文件：

```bash
python3 server/scripts/backup_database.py \
  server/data/experiment.sqlite3 \
  server/backups/experiment-$(date +%Y%m%d-%H%M%S).sqlite3
```

建议在服务器上通过 cron/systemd timer 定期备份，并将备份复制到另一块磁盘。备份文件可以直接用 SQLite 打开恢复。

## 环境变量

见 [`.env.example`](.env.example)。至少需要配置：

- `EXPERIMENT_DB_PATH`：服务器持久磁盘上的 SQLite 文件路径；
- `ADMIN_USERNAME`、`ADMIN_PASSWORD`、`ADMIN_SESSION_SECRET`：管理员登录配置；
- `CLIENT_DIST_PATH`、`PORT`、`CORS_ORIGIN`：生产服务配置；
- `RESEARCHER_ADMIN_TOKEN`：保留给旧脚本和兼容接口的 Bearer 密钥。

不要把真实密码、会话密钥或 Bearer 密钥提交到 Git，也不要把 SQLite 数据库放在可被静态服务器下载的目录中。
