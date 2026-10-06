# Intent Router

路由同时使用 `Task Type + SWT Stage + Known Context + Risk Level`，不得由单个关键词或阶段编号机械决定。

六 Skill 共用的 Decision Record、有限枚举、Materiality 和缺失信息映射见 [decision-model.md](decision-model.md)。记录是可选的内部决策摘要；不输出隐藏推理，也不替代下列路由顺序及各 Skill 的职责边界。

## 路由顺序

`Emergency check → Direct task / Homepage → Known Context → Intent → Stage → Risk → Specialist Skill`

1. 先判断紧急或红色风险并阻止不安全动作。
2. 显式品牌调用优先进入 `swt` 主入口，包括“小How”“小how”“小 HOW”“HowTo SWT”“howto swt”“howto-swt”及“你好小How”“小How你好”“小How你能干嘛”“HowTo SWT 怎么用”等表达。品牌称呼不是首页请求；任务明确时直接路由，不显示首页。
3. 普通“你好”“hello”“hi”“在吗”本身不要求未激活的宿主调用 `swt`；HowTo SWT 已 active 时，普通问候或 help 才显示首页。
4. 从当前 conversation、宿主上下文和已加载材料恢复已知事实，不重复询问。
5. Intent 表示用户此刻想完成什么；Stage 只限制可执行范围；Risk 决定能否给具体操作。
6. 只加载完成任务所需的最少 Skill；多 Intent 可连续调用多个 Skill，由 `swt` 合并。

“小How帮我分析这个 Offer”直接路由 `swt-position`；“小How测一下 Sponsor 面试英语”直接路由 `swt-english`；“小How帮我看看 DS-2019”直接路由 `swt-visa`。这些明确任务不先显示首页。

## Task Type

| Intent | 识别目标 | 默认责任 |
|---|---|---|
| `NAVIGATION` | 我在哪一步、下一步做什么、现在准备什么 | `swt` |
| `DOCUMENT_CHECK` | 某份材料是否完整、正确或可继续使用 | 按文件对象路由 |
| `DECISION` | 在机构、Sponsor、城市、岗位或 Offer 间选择 | 机构／申请链到 application；岗位到 position |
| `INTERVIEW` | 准备或模拟 Sponsor／雇主面试 | `swt-english` |
| `ENGLISH_PRACTICE` | 有目标的口语训练、测评弱项练习、反馈后 Retry | `swt-english` / PRACTICE |
| `INTERVIEW` | 单纯扮演面试官进行 Sponsor／雇主面试角色练习，未要求结构化纠错与 Retry | `swt-english` / INTERVIEW |
| `GENERAL_ENGLISH` | 非结构化口语纠错、工作生活沟通或一般表达优化 | `swt-english` / GENERAL ENGLISH |
| `ENGLISH_ASSESSMENT` | 测试、评分或判断 SWT 场景英语准备度 | `swt-english` / ASSESS；签证事实同时引用 `swt-visa` |
| `FORM_FILLING` | 表格或系统字段怎么填 | 申请系统到 application；签证表到 visa；抵美系统到 arrival |
| `CONFLICT` | 文件、通知、版本、日期或状态不一致 | `swt` 先判风险，再按对象路由 |
| `CALCULATION` | 预算、收入、启动现金或收益情景 | `swt-position` |
| `EMERGENCY` | 人身、医疗、犯罪、即时安全或重大身份紧急问题 | `swt` 先紧急分流，必要时 arrival |
| `GENERAL_QA` | 不属于以上类型的一般 SWT 问题 | `swt`；需专项知识时再路由 |

## 对象与责任

- 简历、视频、Application、Sponsor 系统、雇主申请、Offer 前材料，以及机构／Sponsor 报名、合同与付款：`swt-application`。
- Job Offer 的申请／签署状态到 `swt-application`；岗位、城市、工资、住宿、通勤、二工可行性和收益比较到 `swt-position`。
- Sponsor／雇主面试、口语和工作沟通演练：`swt-english`；结构化短反馈与 Retry 走 `PRACTICE`，只做角色扮演走 `INTERVIEW`。
- “按刚才测评里最弱的两项陪我练”“测完后帮我逐题纠正再重答”：`swt-english` / PRACTICE；读取最近 Assessment Result 但不改其正式分数。
- “陪我练英语”且没有测评结果或具体目标：只问一个一级选择题，让用户选 Agency、Sponsor、Host、Visa 或指定弱项；Host 缺岗位时只补问岗位。
- “练美签口语”进入 Visa Practice：`swt-visa` 核实事实，`swt-english` 训练沟通；事实冲突时暂停优化。
- “测一下机构口语”：`swt-english` / ASSESS with `agency_generic`。
- “帮我模拟 Sponsor 并评分”或“看看我能不能应付 Sponsor 面试”：`swt-english` / ASSESS with `sponsor_generic`。
- “我要面试 cashier，测一下”：`swt-english` / ASSESS with `host_generic`; set Cashier as the position and use job-specific tasks.
- “测一下美签英语”：Visa domain context + `swt-english` / ASSESS with `visa_interview_generic`。
- “综合 SWT 英语测评”：`swt-english` / ASSESS Comprehensive; gather one shared evidence set.
- Host Assessment reuses existing Position Context. Other assessment wording includes “测一下口语”“机构口测”“测我的 Sponsor 英语” and “英语能不能面试 cashier”.
- DS-2019、DS-160、I-901 SEVIS Fee、签证预约、面签材料和跨文件冲突：`swt-visa`。
- “签证需要什么材料”、DS-160 字段、面签事实核对或材料冲突：`swt-visa`，不因出现“英语”路由到 English。若用户同时要求测面签英语，Visa 负责提供／核实事实，English 负责表达测评。
- 行前、机票、入境、I-94、SEVIS Check-in、SSN、保险、抵美后的 Sponsor 要求、换岗二工和项目结束：`swt-arrival`。

SEVIS Fee 与 SEVIS Check-in 是不同任务：前者属于签证链，后者属于抵美报到链。

## 语义示例

- “已经拿到 Offer，下一步是什么”是 `NAVIGATION`，由 `swt` 定位阶段；不能仅因出现 Offer 就调用 position。
- “这两个 Offer 哪个更适合我”是 `DECISION`，调用 `swt-position`。
- “带我逐题练这个岗位的英语回答，每题反馈并让我重答”是 `ENGLISH_PRACTICE` / PRACTICE；若岗位事实尚未核验，可先调用 position。
- “请扮演雇主提问，模拟一轮面试”但没有要求用户重答或逐题反馈，进入 `INTERVIEW`。
- “按我刚才的测评弱项再练一次”“答完告诉我问题并让我重答”是 `ENGLISH_PRACTICE` / PRACTICE；反馈后先 Retry，不能直接跳下一题。
- “陪我做一轮完整 Sponsor 面试模拟”但没有要求测评或逐题 Retry，进入 `INTERVIEW`；用户要求短反馈和 Retry 时改走 `PRACTICE`。
- “我要参加 Sponsor 面试，帮我完整测一次”是 `ENGLISH_ASSESSMENT`，调用 `swt-english` / ASSESS；“模拟 Sponsor 面试”但未要求测评仍是 `INTERVIEW`。
- “我准备面试 Retail Associate，看看我的英语够不够应付这个岗位”调用 `swt-english` / ASSESS，并复用已知 Position Context；没有岗位上下文且任务选择受影响时只问岗位。
- “帮我测一下美签面试英语”由 Visa domain context + `swt-english` / ASSESS 协作；“签证需要什么材料”仍由 `swt-visa` 单独处理。
- “帮我模拟签证官问问题”先由 `swt-visa` 提供／核实签证事实，再由 `swt-english` / INTERVIEW 做真实表达角色练习；没有评分请求时不启动 ASSESS。
- “这个岗位值不值得去，再告诉我面试怎么准备”是 `DECISION + INTERVIEW`，依次调用 position 和 english，整合成一次回复。
- “时薪 16 刀、每周 40 小时、从 6 月 1 日到 9 月 1 日能剩多少”“把房租和税扣掉”“对比两个 Offer 最后剩得多”都是 `CALCULATION`，路由 `swt-position`。日期、周数、税务和汇率缺口按 Choice-first 逐项补足。

## 多 Skill 顺序

先处理紧急和红色风险，再处理阻塞其他任务的前置事实，然后依赖顺序调用必要 Specialist。最终只展示共同结论、必要专项结果和一条合并后的行动清单；事实、风险、问题和作者署名都不得重复。
