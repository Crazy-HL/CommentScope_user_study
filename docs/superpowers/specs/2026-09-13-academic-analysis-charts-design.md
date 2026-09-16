# CommentScope 管理员论文分析图表设计

日期：2026-09-13

## 目标

在不改变参与者端实验流程、实验文章/题目/评论布局和 SQLite 原始数据结构的前提下，完善 `/admin/analysis`：修复论文整体图的底部裁切，按研究者确认的意图为任务级图增加条件均值连线，并把有分析价值的阅读行为、评论交互、主观评价和偏好数据以统一论文风格的图表呈现。

## 约束

- 实验条件仅为 `TE`、`CS`、`SE`、`BL`，显示顺序统一为 `BL`、`SE`、`TE`、`CS`。
- 论文图使用 Arial/DejaVu Sans、黑色细边框、浅灰虚线网格、`coolwarm` 条件色、参与者级散点和均值/中位数及 95% CI。
- 所有图只导出 PNG，导出的是图本身而不是周围的后台控件。
- 模拟数据只用于前端预览，不写入 SQLite；真实模式继续读取现有数据。
- 对时间、准确率、滚动、交互、主观评价等不同量纲，不在同一坐标轴中混合无意义的指标。
- 数据不足时显示现有的缺失/不完整状态，不伪造真实结果。

## 图表范围

### 1. Overall 条件比较图

保留左右两个 panel：

- Overall completion time：条件行、参与者级散点、均值和水平 95% CI；
- Overall task accuracy：条件行、参与者级散点和中位数。

保持参考图的 viewBox 和绘图区比例；将底部刻度和横轴标题放回 viewBox 内，避免文字裁切。

### 2. Task-type accuracy 图

保留三个任务：

- Article Comprehension；
- Comment-Linked Comprehension；
- Comment Location。

每个条件在三个任务位置显示参与者级散点、均值圆点、垂直 95% CI 及上下 cap；根据研究者确认的论文展示意图，连接同一条件在三个任务上的均值点。图例保留 CI、上下 cap、均值点和条件标签。

### 3. 核心结果图

以 2×2 小图展示：

- CTIA；
- CTIRT；
- CLA；
- CLT。

准确率使用 0—1 范围，时间使用秒；各条件使用统一散点、中心趋势和 95% CI。

### 4. 阅读行为图

以独立 panel 或小图展示：

- Initial Reading Time；
- Normalized Scroll Distance；
- Scroll Event Count；
- Page Focus Loss Count。

主要用于解释阅读耗时、导航距离和异常中断，不把辅助指标误称为主要结果。

### 5. 评论交互图

按条件展示有意义的交互指标：

- Comment Interaction Count；
- marker/open/close/click 等计数；
- 评论区域进入次数；
- 评论查看时间。

保留原始事件语义，不把四种条件的不同交互机制简单相加后作同质比较。

### 6. 主观评价图

统一展示 NASA-TLX 六维度、Reading Continuity 和 Comment Accessibility。Mental Demand、Effort、Frustration、RC、CA 作为重点解释指标，其余维度作为补充。

### 7. 偏好结果图

展示四种条件的平均排名、排名分布和第一名比例；偏好理由仍通过数据导出查看，不把文字回答强行数值化。

## 交互和导出

- 每张图提供独立的“导出 PNG”按钮。
- 统一采用高分辨率 rasterize 导出，背景为白色。
- 当前筛选条件和模拟数据开关影响图表数据，但不改变原始数据。

## 数据解释

论文分析页同时保留现有统计表、描述性分析和数据完整性检查。描述性文字明确标注样本量和“非显著性/因果结论”，避免在预测试或小样本情况下过度解释。
