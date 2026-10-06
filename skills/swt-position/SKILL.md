---
name: swt-position
description: 比较 SWT 岗位、Offer 条件、地点、住房、通勤、生活成本、二工可行性与预计净收入；已有 Offer 时用共享州级 SWT Context 辅助判断。适用于“这个岗位怎么样”“值不值得去”“这个地方怎么样”“能赚多少”或“对比两个 Offer”；不负责申请提交、英语训练或签证表格。
---

# SWT Position

目标是在后台排除违反硬条件的候选，面向学生先讲清当前选择及足以改变它的条件，由用户作最终价值判断。

## 开始前

先完整读取 [共享运行规则](references/shared-runtime/swt-position.md)、[岗位与地点核对](references/location-offer.md)、[默认估算数据](references/default-assumptions.json) 和 [预算方法](references/budget-method.md)。需要税务细节时读 [税务估算口径](references/tax-estimation.md) 与 [工作州所得税参考](references/state-income-tax.md)。完整岗位评估中只要有城市、州或可可靠识别的地点，就调用统一入口 `scripts/location_context.py` 获取 state_context 与 swt_market；多岗位比较要逐个岗位解析地点，不能只解析第一个岗位，也不能因岗位多而跳过 Resolver。同一规范化 city/state 可复用同一 context，但各岗位的 Offer 数据仍独立处理。不要分别读取州索引、州 profile、market JSON，也不要复制 Resolver 逻辑。单点问题按需调用、按需回答；没有地点时跳过 Location Context，沿用当前缺值与通用估算规则。岗位／Offer 首答默认使用 `scripts/budget.py` 的 `position_overview` 模式，详情和旧三情景现金流按需展开。

## 工作流

1. 比较单位固定为“岗位＋地点＋住宿＋通勤＋项目日期”，不只比较职位名或州名。
2. 从 Offer 提取雇主、职位、地点、时薪、工时、住房、日期、通勤和其他明确条件；恢复已知年度、预算、底线和优先级，不重复询问。
3. 地点优先级为 Offer 明确地点 → 城市精确解析 → 州级解析 → 通用假设。Offer 明确给出州名或缩写时优先保留该州；有城市和州，或能可靠解析出州时，通过 `get_location_context(city=..., state=...)`（或运行 `python3 scripts/location_context.py --city "<city>" --state "<state>"`）获取统一 context。比较多个 Offer 时，对每个有地点的岗位分别传入该岗位自己的 city/state；不得把一个岗位的州或城市 context 套用到其他岗位。完全相同的规范化 city/state 可复用结果。只有州时只传 `state`；只有城市时只传 `city`，接受 Resolver 的精确结果。`city_ambiguous` 不自行选州；州无法识别时说明无法定位并按现有规则请用户补充，绝不猜测或做 fuzzy 修复。没有 city/state 的岗位不调用 Resolver。
4. 只使用对应岗位的 Location Context 返回资料。state_context 是州级背景，不是城市统计，也不替代 Offer、雇主、住房地址或当季排班事实。state_context 不可用但 swt_market 可用时继续分析；market 数据不能补造州税、最低工资或生活成本。城市为 `state_fallback` 时只用州级资料和明确的区域证据，不生成 city_market。没有地点的岗位沿用现有缺值与通用估算逻辑，不从其他岗位借地点。
5. 先核对资格、日期、班次、体力、住宿、通勤和启动现金等硬条件，标记符合、冲突、待核验。
6. 具体 Offer 数据优先于州级常见数据。Offer 的 `$15/h`、`40h/week` 或 `$100/week` 只能与州级范围比较，例如“高于州级常见时薪”，不得被 State MD 覆盖或改写。
7. 对单岗位、多个岗位、Offer、城市＋岗位和回本问题，按“已知数据 → 州级／城市级参考 → 集中维护的通用估值”补齐普通缺口；时薪与平均工时已知就先算，不因房租、日期、餐费、交通、税费或项目投入缺失而连环追问。真实硬条件冲突与不可逆风险仍先核验。

## 州级 Context 使用

- State MD 的六组字段用于后台估值与六点核心数据的必要简述，不额外生成州级卡。州级数值是“估”，不能冒充城市平均价、本人实际花费或 Offer 条款。
- 用户只问一个具体点时，只读取和回答相关字段。例如“南卡二工好不好找”只回答 South Carolina 的二工信息。
- State MD 中空白或缺失字段在内部仍记为“暂无可靠数据”；只有该缺口会影响本次判断时才向用户说明，不输出一排空字段。
- 已识别州但当前没有对应 State MD 时，用通用规划估值并标“估”；不借用相邻州或其他州资料，也不额外生成州级说明章节。
- 始终使用“州级参考”“South Carolina 的 SWT 样本”等表述；禁止把州级资料写成“某城市平均工资”“某城市统计”或任何城市级结论。
- 州级资料只辅助岗位判断。已核验的零工资所得税州规则集中维护在 `default-assumptions.json` 并注明官方来源；其他州在默认概览中只用显式的规划预留值，不得把 State MD 的税务字段自动当法定税率送入 `budget.py`。旧严格计算模式仍按 `state-income-tax.md` 的已核验范围运行。

## SWT Market Context 使用

- Location Context 是州与城市背景的统一入口。完整岗位评估按需调用 `get_location_context(city=..., state=...)`（或运行 `scripts/location_context.py` CLI）；不要分别读取 `state_summary.json`、`city_summary.json`、`support_groups.json` 或 state_context Markdown。没有地点的 Offer 不调用 Resolver，继续使用现有缺值／通用逻辑。
- `city_exact` 时可结合 state_context、city_market、state_market 与 support context。`state_fallback` 时只用可用的 state_context、state_market 和 regional support evidence；city_market 必须保持为空。state_context 缺失时明确其暂无可靠数据，不用 SWT Market 推断最低工资、州税或生活成本。
- SWT Market 只为 Job、Infra 或必要的地点参考提供背景证据，不增加第七维，不形成分数或推荐。participant count、ACTIVE / INITIAL 与排名只描述当前 BridgeUSA 地图中的参与者计数和数据集内位置；不得据此推断工作好找、二工多、雇主熟悉 J-1、工时或收入更高、岗位更成熟，也不得升级或降低 Offer 结论。
- 引用数字时称“当前 BridgeUSA SWT Map 中的 participant count”或“BridgeUSA 地图参与者计数”，不要写成“该城市每年有 X 个 SWT 学生”。该计数目前未验证为年度去重参与者人数；排名仅相对当前数据集。
- `city_exact` Support Group 可表述为官方清单中的明确城市记录。`regional`、`multi_city`、`county_or_region`、`affiliate` 只能作为区域基础设施 evidence；`unmatched` 不得绑定城市。区域记录不能改写为“该城市有官方支持组织”。
- 只有完整岗位评估才在六维核心表之后按需加一个轻量的 `### SWT 地点背景`，最多 3–4 行，限于实际可用的 city/state participant count、city rank 与 Support evidence。若无 city exact 数据或仅州级命中，不填造城市行。附注 participant count 为 BridgeUSA SWT Map 查询返回的计数，不等同于年度去重参与者人数。单点问题不机械展示此块。
- 多个 Offer 并列时，对每个不同地点分别保留 Resolver 结果。仅当岗位数不少于 2 且至少 2 个岗位的 `swt_market` 可用时，才可在六维主表之后加一张轻量 `### SWT 地点背景` 对比表；它是辅助地点资料，不替代六维主表、回本表或注意事项表。同一 city/state 的多个岗位可共用一行地点背景，但在六维、回本和注意事项表中仍各自保留。地点背景表列为 `地点`、`City participant count`、`State participant count`、`City rank`、`Community Support`。城市没有 exact market 时 City participant count 和 City rank 写 `-`；州市场缺失时 State participant count 写 `-`；未知值不写成 0。`city_exact` 支持标 `City exact`，区域支持标 `Regional evidence`，没有可用支持证据写 `-`。state_context 不可用的岗位仍可列入，只展示实际可用的 market 字段；州税、最低工资和成本仍按原缺失规则处理。整表后只加一条计数口径短注。
- SWT Market 不进入任何岗位的收入、税费、生活成本或回本计算，也不用于 Offer 排序、推荐或好坏结论。多岗位比较的结论和任何既有排序只能来自 Offer 条件及原有预算／岗位分析逻辑；participant count 高低不得改变顺序、评分、二工判断或岗位成熟度判断。
- 不新增第二张 State Reference Card。若用户追问时已展示州级参考，将 SWT Market Context 放在同一地点参考中，并区分来源：最低工资、州税等来自 state_context；participant count / rank 来自 BridgeUSA SWT Market；Support Group 来自 BridgeUSA Community Support Groups 清单。

## SWT 预计净收入计算器

凡是语义上在问“这个岗位怎么样”“哪个 Offer 更适合”“能否回本”“最后剩多少”或“扣房租和税”，默认进入本 Skill 的岗位概览模式；不要要求固定关键词。

1. 先复用已知 Offer、时薪、工时、日期、房租、州、成本、汇率和税务信息。用户已给出字段时不得重复问。
2. 工作期按用户日期 → Offer 日期 → 用户周数 → 集中默认周数；普通费用按岗位／用户数据 → 精确城市参考 → 州级参考 → 通用规划估值。已给真实房租或餐费立即覆盖估值；换工时只重算受影响项。缺口来源记录在计算结果里，前台只用“估”标记与一行必要说明。
3. 税费列必须给规划估算值：优先本人已知税务数据，再按当前 J-1／非居民规则、可核验的州税结论和集中默认税务模型计算。默认模型有税务身份、税年、无协定优惠等前提；不能把预估税费说成最终税额或实时工资单扣缴。
4. 只问一个用户接下来想展开的一级选择题（3–5 个选项）；用户追问某一项时只展开该项，不重复整个首答。若时薪或平均工时本身都没有，才先问最关键的一项；加班无明确薪率时不自行假设。

## 默认前台结构

**一句话结论**，随后按 `## 1. 核心数据`、`## 2. 回本测算`、`## 3. 注意事项`、`## 4. 继续看什么？` 输出。核心数据主表的六个维度固定为收入、住宿、生活成本、交通、二工、落地便利；回本表列税前工资、预计税费、生活成本、前期投入、最终预计结余和回本周数；注意事项只横向比较真实重要的问题，无该问题填 `-`。多 Offer 比较仅在达到上述条件时，可在六维主表之后、回本测算之前插入轻量 `SWT 地点背景` 辅助表，不新增编号部分或第七维。表格单元格短，估值标“估”；表后不重复解释注意事项。第四部分只留一个 3–5 选项的一级问题。单点问题不输出整表或地点背景。不得添加重复州级卡；其余口径、证据、风险或方法论章节留待追问。

当前汇率不是静态知识。用户指定汇率时直接使用；用户要求“当前汇率”时，先核验当轮可靠来源并显示汇率与时间，无法核验则先输出美元并标记人民币待补。

## 边界

- 普通成本未知时使用有来源层级的估值，不默默补零；押金、小费和未经批准的二工收入不进入默认回本基础值。默认项目费、汇率与税务预留只是规划值，不是市场平均、合同价或个人最终税额。
- 区分“等 SSN 期间不能开工”与“已工作但工资延后发放”：后者影响到手现金和首薪前准备，不自动减少最终应得工资；只有明确无法收到的证据才计作收入损失。
- 联邦所得税、工资单预扣、最终税负和退税不是同一概念。按集中维护的年度税阶与适用前提估算联邦税；不能永久硬编码联邦 10% 或把通用州税预留率称为当地税率。
- “允许二工”不等于已批准或可开工；实际审批与在美变更属于 `swt-arrival`。
- Offer 的申请、签署和系统状态属于 `swt-application`；面试训练属于 `swt-english`。
- 不用总分、星级或未经验证的成功概率替代用户取舍。

最终面向用户输出前执行共享 Creator Attribution 规则；若由 `swt` 统一整合，本 Skill 不单独输出署名。
