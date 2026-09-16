# 自适应论文分析图表类型设计

## 背景

管理员论文分析页当前将大多数指标统一呈现为“参与者散点 + 中心趋势 + 95% CI”。这种方式适合保留原始观测分布，但不适合所有指标：离散准确率、次数统计、偏好排名和偏态行为数据需要不同的视觉编码，才能更直接地支持论文分析。

本次改造只调整管理员论文分析页的可视化呈现方式，不改变参与者端实验流程、实验材料、题目、评论嵌入方式、SQLite 原始表结构或数据采集逻辑。

## 目标

1. 按指标的数据性质选择合适的图表类型。
2. 保留用户提供的 Matplotlib 参考风格作为统一视觉语言。
3. 保留参与者级信息、均值/中位数和误差范围等论文分析所需信息。
4. 每张图都能独立导出为 PNG，方便直接用于论文排版。
5. 模拟数据仅用于视觉预览，不写入 SQLite。
6. 小样本真实数据不显示误导性的推断性置信区间；正式样本量达到设计要求时使用 t-based 95% CI。

## 非目标

- 不新增 `mode = pilot` 或其他实验模式。
- 不改变管理员登录、数据筛选、数据导出和参与者端流程。
- 不将模拟数据写入后端或数据库。
- 不输出 PDF、SVG 等格式；本阶段只需要 PNG。
- 不把交互次数、滚动次数等辅助指标解释为主要因果结果。

## 统一视觉规范

所有图表使用同一套论文风格：

- 白色背景；
- Arial / DejaVu Sans 无衬线字体；
- 深色细坐标轴；
- 浅灰色虚线网格；
- coolwarm 条件配色，条件顺序统一为 BL、SE、TE、CS；
- 统一的标题、轴标签、字号和留白；
- 数值标签只在不遮挡数据的情况下显示；
- 导出 PNG 时保留 SVG 内嵌样式，避免导出后字体、颜色或线型丢失；
- 导出画布需要包含完整轴标题、刻度、图例、任务标签和注释，不允许底部文字被截断。

## 图表类型分配

### A. 参考代码风格的核心论文图

#### Overall completion time

使用参与者级散点图，按条件分行展示：

- 每个参与者一个散点；
- 条件均值黑点；
- t-based 95% CI；
- 均值标注 `M=...`；
- 时间横轴；
- `Lower is better` 色带。

#### Overall task accuracy

使用参与者级散点图，按条件分行展示：

- 每个参与者一个散点；
- 条件中位数黑点；
- 中位数标注 `Mdn=...`；
- 准确率横轴固定为 0.50、0.75、1.00 的紧凑论文显示范围，同时保留观测值；
- `Higher is better` 色带。

#### Task-type accuracy

使用与参考代码一致的均值连线散点图：

- 横轴为 Article Comprehension、Comment-Linked Comprehension、Comment Location；
- 每个条件一条均值连线；
- 显示参与者级散点；
- 显示条件均值点和 95% CI；
- 顶部统一图例；
- 任务标签和图例不被 SVG 边界裁切。

### B. 核心结果图

#### CTIA

使用参与者级散点 + 均值 + 95% CI：

- y 轴固定为 0—1；
- `Higher is better`；
- 保留每个条件的原始观测点和样本量。

#### CTIRT

使用参与者级散点 + 均值 + 95% CI：

- 时间统一转换为秒；
- `Lower is better`；
- 保留每个条件的原始观测点和样本量。

### C. 离散任务准确率

#### CRA、ACA、CLA

使用分组柱状图：

- 每个条件一根柱；
- 柱高为条件平均准确率；
- 误差线为 95% CI；
- 柱顶显示平均值；
- y 轴固定为 0—1；
- 使用条件对应的 coolwarm 颜色；
- 数值表继续显示 n、均值和 CI。

选择柱状图的原因：这三个指标的区块级得分取值离散且范围固定，平均准确率的条件比较比连续散点更容易阅读。

#### CLT

使用箱线图：

- 每个条件一个箱体；
- 显示中位数、四分位距、须线和异常值；
- 时间单位为秒；
- `Lower is better`。

### D. 阅读行为数据

以下指标使用箱线图：

- Initial Reading Time；
- NSD；
- Scroll Events；
- Total Scroll Distance；
- Max Scroll Y。

原因：阅读行为和滚动行为通常可能偏态或存在极端值，箱线图比单纯均值柱状图更能表达分布。

### E. 评论交互数据

以下指标使用分组柱状图：

- Comment Interaction Count；
- Comment Click Count；
- Comment Open Count；
- Comment Close Count；
- Paragraph Toggle Count。

每个条件显示平均次数和误差线。该组图明确标注为辅助行为指标，不将其与 CTIA/CTIRT 作为同等重要的主要结果。

### F. 主观评价

以下指标使用评分柱状图：

- Reading Continuity；
- Comment Accessibility；
- NASA-TLX Mental Demand；
- NASA-TLX Effort；
- NASA-TLX Frustration；
- NASA-TLX Physical Demand；
- NASA-TLX Temporal Demand；
- NASA-TLX Performance。

规则：

- RC、CA 的 y 轴固定为 1—7；
- NASA-TLX 的 y 轴固定为 0—100；
- 显示均值和 95% CI；
- RC、CA、Performance 使用 `Higher is better`；
- NASA-TLX Demand、Effort、Frustration、Physical Demand、Temporal Demand 使用 `Lower is better`，但 Performance 除外。

### G. 偏好结果

#### Preference Ranking

使用水平条形图：

- 每个条件一条水平柱；
- 显示平均排名；
- 排名轴为 1—4；
- `Lower is better`；
- 保留平均排名数字。

#### First-place Share

使用水平条形图：

- 每个条件一条水平柱；
- x 轴固定为 0—1；
- 显示第一名比例；
- `Higher is better`；
- 保留比例数字。

## 数据与统计规则

1. 所有图表使用管理员接口返回的真实统计观测值。
2. 模拟数据只由前端内存生成，用于预览图形，不进入 API、不进入 SQLite。
3. 当某条件观测数小于 4 时，不显示 t-based 95% CI，数值表显示 `—`，避免 n=1 或 n=2 时出现夸张区间。
4. 正式实验样本量达到 24 名参与者、每条件 24 个文章区块后，使用 t-based 95% CI。
5. 柱状图的误差线和散点图的误差线采用相同的 CI 计算规则。
6. 箱线图不使用均值替代分布；如需要辅助说明，可在图旁显示 n 和中位数。
7. 过滤器仍然作用于真实数据，图表的 n、统计量和导出内容必须同步更新。

## 导出要求

每个图表组件均提供“导出 PNG”按钮：

- 导出当前筛选范围和当前模拟/真实数据状态；
- 文件名包含指标名称；
- 导出分辨率适合论文插图；
- 导出结果不能截断底部标题、任务标签、图例或注释；
- 只生成 PNG，不再生成 PDF/SVG 下载文件。

## 验收标准

1. Overall 两张图仍与用户参考 Matplotlib 风格一致。
2. Task-type accuracy 显示四条条件均值连线。
3. CRA、ACA、CLA 为柱状图，不再使用统一散点图。
4. CLT 和阅读行为指标使用箱线图。
5. 评论交互指标使用柱状图。
6. RC、CA、NASA-TLX 使用评分柱状图。
7. Preference Ranking 和 First-place Share 使用水平条形图。
8. 所有图拥有独立 PNG 导出按钮。
9. 所有图的视觉样式一致。
10. 浏览器检查不存在 SVG 外部文字裁切。
11. 模拟数据预览下每个条件有 24 个观测，不修改 SQLite。
12. 现有管理员、实验流程和后端测试保持通过。
