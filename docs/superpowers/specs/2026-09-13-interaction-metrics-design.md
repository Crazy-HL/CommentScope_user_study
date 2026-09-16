# 文章与题目交互指标记录设计

日期：2026-09-13
状态：已确认，进入实现

## 目标

在不改变实验流程、题目内容和参与者界面的前提下，完整保留文章阅读阶段与答题阶段的原始交互，并可以按参与者、文章、实验条件、阶段和题目进行汇总统计。

## 记录原则

1. 原始事件表继续保留每次可解释的交互，作为审计和重新计算的唯一事实来源。
2. 文章区块表保存阅读阶段的常用汇总，便于管理员后台直接查询。
3. 题目回答表保存每道题的选项点击次数与答案修改次数。
4. 所有事件带有 `article_order` 与 `stage`，避免把同一篇文章不同阶段的行为混在一起。
5. 不记录页面空白处、浏览器控件等无解释价值的全局鼠标点击，只记录评论交互、段落评论切换、题目选项选择等实验相关行为。

## 文章阅读指标

`article_sessions` 增加：

- `scroll_event_count`：前端节流后保存的滚动采样事件数；
- `total_scroll_distance_px`：相邻滚动位置变化的绝对值之和；
- `max_scroll_y`：阅读阶段观察到的最大滚动位置；
- `comment_click_count`；
- `comment_open_count`；
- `comment_close_count`；
- `paragraph_toggle_count`。

现有 `normalized_scroll_distance` 与 `comment_interaction_count` 继续保留，保证旧数据兼容。

## 题目交互指标

答题阶段如果 ACA、CTIA 或 LOCATION 仍显示文章区域，也按当前题目记录该文章区域的滚动行为；CRA 没有文章区域，因此对应滚动指标为 0。

每次题目选项点击或改变时保存 `question_option_change` 事件，事件负载包括：

- `question_type`；
- `question_id`；
- `item_index`；
- `selected_option`；
- `stage`。

`responses` 增加：

- `option_click_count`：提交前点击答案选项的总次数；
- `option_change_count`：实际从一个选项切换到另一个选项的次数；
- `scroll_event_count`：当前题目期间文章区域的滚动采样事件数；
- `total_scroll_distance_px`：当前题目期间文章区域的滚动距离；
- `max_scroll_y`：当前题目期间文章区域的最大滚动位置。

既有最终答案、正确性、开始时间、提交时间和答题耗时不变。

## 阶段标识

事件阶段使用：

- `reading`
- `cra`
- `aca`
- `ctia`
- `location`
- `survey`

## 统计方式

文章级统计键为：

`session_id + article_order + article_id + condition`

题目级统计键为：

`session_id + article_order + article_id + question_type + question_id`

管理员后续可按文章区块直接显示滚动次数、滚动距离、评论点击分类和答题结果，也可以通过原始事件追溯具体操作序列。

## 兼容与迁移

数据库初始化时使用幂等的 `ALTER TABLE ... ADD COLUMN` 迁移，为已有 SQLite 文件补充新字段；不删除现有记录，不改变现有实验流程。旧客户端未发送新字段时，服务器使用默认值或从现有事件兼容计算。
