# SWT Market Data Methodology

## 数据来源

- 数据来源：BridgeUSA Summer Work Travel Participants Map
- 发布机构：U.S. Department of State
- participant count 来源：BridgeUSA SWTDashboard Power BI 查询返回值
- Community Support Group 记录来源：官方 Community Support Groups 清单，经 cleaned 层保留的记录与匹配字段
- 运行层输入：插件目录外 `swt-data-source/SWT_MAP_DATA/cleaned/` 中的州级 JSON、城市级 JSON、Support Groups CSV 和 source metadata

具体 source URL、数据集刷新时间、抓取时间及原始字段定义见 `source_metadata.json`。本知识层只投影已验收的 cleaned 聚合字段，不重新清洗、不重新分组、不修复 manual_review 项。

## participant count

`active`、`initial` 和 `total` 均来自 BridgeUSA Power BI 查询返回的 participant count。`total` 保留 cleaned 输入中的聚合值。

目前没有证据证明 `total` 等同于去重后的年度独立 SWT 参与者人数。因此 Skill 应优先表述为：

- BridgeUSA SWT Map participant count
- BridgeUSA 地图参与者计数
- 当前官方地图中的 SWT presence / participant count

不要表述为：

- 该城市每年有 X 个 SWT 学生
- 该州有 X 个唯一参与者

除非未来获得独立验证。

## 州与城市排名字段

`top_city_record` 只表示该州当前数据中 participant count 最大的 city record。它不表示最热门、最推荐、工作机会最多或收入最高。

`national_rank_by_total` 与 `state_rank_by_total` 仅表示 cleaned 数据中 participant count 的排序位置，不构成质量或推荐评分。

## Support Group 记录数量

`support_group_record_count` 只表示该州在官方 Community Support Groups 清单中的记录数量。该数值不表示成功覆盖的城市数，也不表示服务质量或实际可用性。

## Support Group 匹配

- `exact`：可以视为明确城市匹配。
- `multi_city`、`regional`、`county_or_region`、`affiliate`：只能作为区域性基础设施证据，不能据此断言某一单独城市一定有该组织。
- `unmatched`：不得强制绑定某城市。

保留 cleaned 输入中的所有类型与匹配状态，不对 `manual_review` 中的问题做自动修复或重新绑定。当前需特别保持：

- `Door County, WI`：`county_or_region` / `unmatched`。
- `Door County Affiliate, WI`：`affiliate` / `unmatched`。
- `Bethany Beach and Fenwick Beach, DE`：`multi_city` / `low`，只保留 cleaned 中的部分匹配。
- `Cape Cod Affiliate - Dennis, Not West Yarmouth, MA`：`affiliate` / `regional` / `low`。

## 字段与范围

州级与城市级 summary 保留 cleaned 输入提供的 participant count、记录数、地理字段、排名和来源时间字段。字段值不在本层重新计算。`city_summary.json` 中的 `total` 表示 BridgeUSA SWT Map participant count 聚合值，不表示年度唯一参与者人数。

本层不包含 3649 条原始点位，也不复制 raw Power BI JSON。其数据范围限于州级、城市级聚合与 Support Group 清单记录。
