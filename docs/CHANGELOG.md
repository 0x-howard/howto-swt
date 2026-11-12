# HowTo SWT 更新记录

## v1.6.1

- 不叫“小How”也能用：说正在准备 J-1 SWT、不知道从哪开始或问全流程怎么走，会进入主入口
- 问“我现在该做什么”或“全流程怎么走”时，先给四行现状：在哪一步、已经完成什么、卡在哪里、下一步做什么，并标明这是假设；全流程按 8 个阶段各讲一句
- 一次问好几件事时，开始前先写三行：收到什么、先做哪个、为什么这样排；学生已经做完的步骤跳过
- 学生说理解错了，或新事实推翻了前提时，先说明改了哪个判断，再换功能继续；只是补充材料不因此换功能
- 六个专项功能各自写明：学生带到什么程度才开始、交出什么结果、哪些事不做
- 紧急情况的第一句先给行动：到安全的地方、打 911、联系 Sponsor 的 24 小时电话；联系不上时打 J-1 紧急热线 1-866-283-9090
- 首页加了可以直接照着说的例子；“不确定”里多了“项目快结束，准备回国”

## v1.6.0

- 子 Skill 从 5 个增加到 6 个，新增 `swt-yangmao`（省钱赚钱）：帮带、纽约测试（uTest、Focus Group）、教堂免费餐和 Food Pantry、九价 HPV 疫苗、网购返利
- `swt-visa` 新增加拿大签证：判断能否用有效 J1 美签走 CAN+ 简化申请，讲申请时机、费用和在美国用 USPS 寄护照贴签
- `swt-arrival` 新增在美证件和账户指南：驾照、州 ID、J1 转 F1、电话卡和回国保号、银行开户奖励、信用卡、美股券商和税务，并给出到美国后先办哪个的顺序
- “羊毛”按对象分流：银行、信用卡、电话卡、证件的羊毛进 `swt-arrival`，加拿大签证进 `swt-visa`，其他省钱赚钱进 `swt-yangmao`；问“附近”时给全国性银行的开户奖励和官方网点查询入口，不编造网点
- `swt-application` 新增合同雷点检查：先确认合同是否完整、是否已签，按“条款｜风险｜建议”三列逐条拆解，附退款时间线；不复述合同里的个人信息
- 主入口首页改为 7 个数字选项，“不确定”时先问到了哪一步再分流；面向宿主的说明不再混进菜单
- Free 版广告改由脚本控制，每天第一次使用时出现一次，同时作为当天署名；其他回复不出现广告
- 更新提醒改为回复「更新」才执行，回复数字一律按菜单选项处理

## v1.5.3

- 口语测试开场先问按哪种面试来测（机构、Sponsor、雇主、签证或综合）
- 支持语音输入：按语音转写文字评估，识别错误不扣分，口头填充词和重来作为流利度参考
- 测评结果统一格式：一句结论、分数表、最多三个弱项、限制说明和后续选项，标签改为中文
- 语音聊天时每轮只说一句问题，结束时先说结论

## v1.5.2

- 岗位分析重新排版：开头一句加粗结论，分为六维分析、回本测算、特殊注意事项三部分
- 回本测算改为每周账和回本进度条，并说明每周要工作多少小时才能在工期内回本
- 六维分析的分析列根据州级数据写出与当地常见时薪、周租的对比和税费、销售税、公共交通等要点
- 比较多份 Offer 时每个维度拆成小行，差距统一写进“对比要点”，共同条款与各岗位独有条款分开列
- 2–3 份 Offer 显示工时与结余的折线图；终端里可另存为图片
- 4 份及以上 Offer 先问赴美核心诉求（多赚钱、省心与安全、旅行与体验、提升英语），再按诉求选出 3 份深入对比
- 新增 Offer 字段提取模板；读不到的关键信息直接请你看一遍 Offer 补充
- Offer 写明工时区间时，另给按最低工时计算的结余

## v1.5.1

- 新版本提醒会说明新版本多了什么；回复 `1` 或说“更新小How”，小How 直接帮你更新
- 修正只安装 `swt` 时版本检查找不到版本号的问题
- Codex 的 Skill 列表里显示中文用途，例如 `swt-position（岗位分析）`
- 6 个 Skill 的说明改成大白话
- 一次用到多个 Skill 时，先说明先后，最后写明用了哪些
- 补充 Windows 安装说明

## v1.5.0

- 可以直接发 Offer 的 PDF 或截图，小How 会逐页整理工资、工时、住宿等信息，并标出来源
- 人民币换算使用当天查到的 USD/CNY 汇率，向上取一位小数；查不到汇率时，美元部分照常计算
- 金额统一保留两位小数；超过工期还回不了本时直接说明
- 新增 Cursor 等 Agent 的使用方式
- 重写 README 和使用文档，更简洁

## v1.4.0

- 说清任务就直接交给对应 Skill，不再先显示首页或要求复制提示词
- 岗位分析改为六个方面（收入、住宿、生活成本、交通、二工、落地便利）加两张回本表
- 只看一份 Offer 时不显示收益函数，比较 2–3 份时才显示
- 重做 README 首页

## v1.3.0 — Offer Return & Interaction Capability

### Milestone 5 — Offer Return Function

- `swt-position` 新增确定性岗位收益函数 `y = ax + b`：斜率表示每增加一小时的预计税后收入，截距表示每周固定生活成本基线。
- 支持可信的最小／预期／最大工时、函数交点、关注区间 upper envelope、严格支配识别与 `Wage → Max Acceptable Rent` 边界函数；缺失估值继续明确标“估”。
- 1–3 个岗位可比较收益曲线；超过 3 个岗位先列全量表格，再通过最多 3 项的选择进入函数比较。图形不可用时完整退化为函数、交点、区间结论和表格。

### Milestone 6 — Cross-Agent Interaction Layer

- 建立共享 Interaction Request / Adapter Contract，统一 `single_choice`、`multi_choice`、`free_text`、`structured_form` 与 `confirmation`，并按宿主能力选择原生 UI 或文本 fallback。
- Router 的 `DIRECT / CONFIRM / CLARIFY` 接入交互层：已明确就执行，有限选择优先 picker，需要事实则输入；Pro 已知上下文不会重复询问。
- Codex 当前会话、Claude Code、WorkBuddy 与豆包 Work 分别记录能力证据与降级边界；静态或 mock 验证不会冒充真实宿主 UI 验证。

- 主入口改为严格两阶段 Router：生成包含任务、上下文、边界、节奏与输出要求的 Handoff Prompt 后停止，等待用户确认／修改／重新发送后再由 Executor 执行。
- 扩充 HowToSWT／howtoswt／小How等入口变体；无任务问候显示六项菜单，带任务输入直接生成目标 Handoff，不再先展示首页。
- Free 主入口在 Handoff 或菜单之后、Contract 之外最多显示一次固定两行 Pro 提示；Pro 构建会移除该区块，子 Skill 与英语执行模式均不显示。
- 将 `swt-english` 升级为六模式 SWT AI Speaking Coach：Profile-driven Mock、每题最多三次动态追问、Practice／Mock 分离、统一七维 Assessment、Recording 证据降级、Retry 与 Progress。
- Free 保留当前 conversation 内的完整 Profile → Mock → Assessment → Retry 闭环；Pro Progress 接入既有 Lifecycle Context，不建立第二套长期存储。

## v1.2.0 — Task, Context & Runtime Architecture

### Milestone 1 — Orchestration Architecture

- 将 `swt` 收敛为 Orchestrator / Router，使用 `DIRECT / CONFIRM / CLARIFY` 三种路由模式，不再承载岗位、英语或签证等下游业务实现。
- 建立统一 Handoff Contract，并为 Application、Position、English、Visa、Arrival 五个 Executor 定义有限状态机与越权边界。
- 保留并回归已有 Position、English、Visa 行为；已知上下文不重复询问，`changed_facts` 明确覆盖旧事实。

### Milestone 2 — Pro Lifecycle Context boundary

- 固定 Free 为当前会话内的 ephemeral task context；为 Pro 定义 package 外的 canonical Profile、SWT Case、Lifecycle、Domain Records 与 Event History 接口边界。
- Context Builder 只选取当前 Executor / intent 所需资料；Write Back 只持久化 confirmed fact 或带来源与 confidence 的 evidence fact，inference 必须先确认。
- Pro 的实现保留在私有 overlay；Free 不依赖 Pro context，也不包含 Pro 私有源码或用户长期数据。

### Milestone 3 — Distribution Guard & Runtime Lifecycle

- Free 新增基于公开 `runtime-manifest.json` 的 SemVer 更新检查、24 小时 cache 与 fail-open 状态；check 与 apply 强制分离。
- 建立跨 Edition Runtime Identity、显式替换确认、WorkBuddy flat-six adapter、stage / validate / backup / replace / verify / rollback 契约，由公开 CLI 实现受控安装。
- 明确第三方 Skills CLI 的技术边界：一般 Agent 使用 preflight，受控 CLI 与 WorkBuddy 路径使用 hard guard。

## v1.1.1 — Runtime Activation & README Homepage Cleanup

- 修复“小How / HowTo SWT”显式称呼未能触发主 Skill 的 discovery 问题；在入口 description、plugin manifest 和生成的主入口规则中加入调用别名。
- 明确普通 greeting 不会抢占未激活的宿主；已激活后可进入首页，明确任务直接路由到对应 Specialist。
- 将 Home 改为简短任务菜单，避免在用户已经称呼小How后重复介绍 Persona。
- 将 README 重构为面向公开用户的 GitHub Landing Page，加入快捷导航和“工作目标 → 主要入口 → 常见产出”能力表。
- 改用 Skills CLI 安装入口；为六个 Skill 生成独立安装所需的运行资料和脚本，不带入测试与开发工具。
- README 只展示最近五条更新，完整历史仍保留在 CHANGELOG。
- 将新手指南、架构、数据隐私和开发说明迁至 `docs/`，规则真源仍由原有 `shared/` 与 `references/` 维护。

## v1.1.0 — Naming Unification

- 正式统一产品品牌为 `HowTo SWT`。
- 将 README 中的 GitHub repository 目标名称、本地项目目录与 package / plugin identifier 统一指向 `howto-swt`，并同步本地 marketplace metadata；SWT Skill 保留为产品类别描述。
- 统一 Persona 为“小How”、Creator 为 Howard，并更新 README、manifest、安装说明、测试、文档和 generated metadata 中的当前产品级名称。
- 保留六个内部 Skill 名称不变，避免无意义的路由和接口迁移。
- 保留历史 CHANGELOG 名称，记录项目演进；增加面向 J-1 Summer Work Travel 的 SEO / GEO 描述，不修改正式品牌名。

## v1.0.0 — howto-swt.skill Production Architecture

- Renamed the user-facing product to `howto-swt.skill` and introduced the assistant persona “小How”; retained the `swt-plugin` package identifier for existing marketplace compatibility.
- Defined separate Runtime, Source, Test, and User Data boundaries. Moved raw SWT Map source snapshots and cleaning inputs out of the installable Skill tree while retaining normalized runtime summaries.
- Added opt-in persistence through an explicitly configured external `USER_DATA_ROOT`, a minimal allowlisted state schema, atomic JSON storage, and sensitive-field rejection. No default path or repository fallback is used.
- Moved SWT Map build-time inputs and intermediate products to the sibling `swt-data-source/`, added a hash-backed source manifest, retained only normalized runtime data in the product, and changed generated eval reports to temporary output while keeping necessary synthetic fixtures.
- Updated README, manifests, shared runtime and validation contracts; the six-Skill architecture and v0.7/v0.8 English Assessment and Practice models remain in place.

## v0.9.0 — Structured Decision Architecture

- Added `shared/decision-model.md` as the shared source for finite intent, route, stage, confidence, risk, evidence, materiality, missing-information and next-action values.
- Added an optional minimal Decision Record and deterministic validation rules for critical conflicts, emergency risk and English Assessment/Practice routing.
- Mapped missing-information classes to the existing clarification Levels 1–4 without replacing existing interaction or risk policies.
- Kept the six Skills, English Assessment Rubric, four Profiles, Assessment Result Schema, and v0.8 Practice behavior unchanged.

## v0.8.0 — SWT English Practice

- 在 v0.7 English Assessment 基础上增加场景化口语训练闭环，通过 Assessment Result 自动选择弱项，支持 Agency、Sponsor、Host 和 Visa 四类 Practice、动态追问、短反馈、Retry 和 Reassessment。
- 为四类 Practice 复用既有 Assessment Profile 与 question-bank；增加 FULL MOCK、WEAKNESS DRILL、FOLLOW-UP DRILL、QUESTION DRILL 和 SCENARIO DRILL，不新增 Skill、题库、Rubric 或 Assessment Result Schema。
- 增加独立的最小 `english_practice` 状态；按最高影响问题给短反馈、鼓励用户自行重答，记录 before／after 改善但不覆盖正式 Assessment。
- 更新 English 路由、v0.8 行为验收场景、README、plugin manifests 和生成的 shared runtime 版本标记。

## v0.7.0 — SWT English Assessment

- Added `ASSESS` to the existing `swt-english` Skill: four generic scenario profiles plus a one-session Comprehensive Assessment, using one shared seven-criterion evidence set.
- Added actionable seven-dimension scoring anchors, evidence/confidence/input-mode rules, adaptive question types, compact first-result output, fact-conflict handling for Visa communication, and IELTS-style estimates with explicit non-official limits.
- Added deterministic profile Readiness weighting in `scripts/speaking_score.py`; missing or undersampled criteria produce a partial result.
- Kept the existing six-Skill plugin layout and the prior English interview, correction, follow-up, and general SWT communication capabilities.

## v0.6 — SWT Market / Location Data Layer

Recorded from the current project files and source artifacts; no earlier release log was used to infer unimplemented features.

- Added the `swt_market` reference layer generated from `SWT_MAP_DATA/cleaned/`, containing BridgeUSA map state/city aggregates and Community Support Group records, with indexes, source metadata, and methodology.
- Current cleaned artifacts report 51 state rows, 2,465 city rows, and 15 Community Support Group records. The associated quality report records 3,649 retained map point rows, matching participant-count totals before and after cleaning, and four Support Group entries retained for manual review.
- Added source-specific limits for interpreting participant counts and matching regional, affiliate, and multi-city support records; these are background context, not offer recommendations or unique annual participant counts.
- Added data cleaning/build scripts and connected the resulting state and market context to the existing SWT specialist workflows.

## v0.5 — Decision Output & Budget Model

- Added a six-dimension position comparison output, after-tax break-even / project balance calculations, labeled default estimates for missing ordinary budget inputs, and progressive detail expansion.
- Added tax-mode distinctions and warnings for planning estimates, missing data, and Sponsor approval boundaries.

## v0.4 — State-first Position

- Added state-level SWT context and location resolution, state reference material, and reusable position budget inputs to support state-aware comparisons.

## v0.3 — Six-Skill Architecture

- Established the six existing Skills: `swt`, `swt-application`, `swt-position`, `swt-english`, `swt-visa`, and `swt-arrival`, with routing and specialist boundaries.

## v0.2 — Position Prototype

Reconstructed from development history; original Codex logs incomplete.

- Began structuring position choice as a distinct module, providing a base for the later `swt-position` Skill.

## v0.1 — Personal Experience Prototype

Reconstructed from development history; original Codex logs incomplete.

- Organized Howard's early SWT application, position selection, interview, arrival, and work experience into the initial SWT Skill.
