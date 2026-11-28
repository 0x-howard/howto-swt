# 国内机构公开价与口碑数据

供 **`swt-application`** 选机构／比价／看避雷，以及 **`swt-position`** 测算前把项目费默认值接到机构对照表。

数据来自 2026-11-27《SWT 机构调研 · 交叉验证》蒸馏。

- 机器可读：`agencies-market-2026.json`／`.csv`
- 脚本：`python3 scripts/agency_market.py --name 西米` 或 `--list`；测算默认价用 `--planning-fee 西米`
- 人读摘要：`swt-application` 的 `references/agency-market-2026.md`

**字段**：`price` 保留公开冲突原文；`planning_default_cny` 是岗位测算用的单一人民币规划默认（估），不是合同价。无单一口径时为空，测算回退通用默认。

**规则**：价格带年份；避雷是「有人在说」；冲突原样列出；不替学生选型付款。
