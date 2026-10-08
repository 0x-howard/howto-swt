# 变量与状态恢复

每个变量在后台记录 `值／单位或口径／硬底线或软偏好／来源／未知项`。不得把空白视为不限制，把“希望”自动升级成不可接受条件。变量是内部状态清单，既不是默认问卷，也不是最终回答提纲；先复用对话和材料中的已知信息，只追问会改变本次判断的缺口。

## 状态范围

默认只恢复当前 conversation、宿主已提供的上下文和用户主动加载的数据。不要声称自动记住其他 conversation。真正的跨 conversation 自动恢复必须由独立 Persistence Layer 实现，并明确保存、更新与删除边界。

v1.0 的可选跨 conversation 存储契约见 [persistence-contract.md](persistence-contract.md)，字段限于 [user-state.schema.json](../references/user-state.schema.json)。未显式配置外部 `USER_DATA_ROOT` 且用户未要求保存时，状态仅属于当前 conversation；不得回退写入插件目录。

## 共同变量

| 变量 | 具体收集内容 | 用途 |
|---|---|---|
| 【项目年份与当前阶段】 | 咨询、已报名、口测、已拿 offer、已付款、在美；决策截止日 | 使用正确年份，避免建议错过节点 |
| 【学校与学籍】 | 就读国家、学校名称（确需核验时）、课程形式、全日制状态、已完成学期、预计毕业时间 | 比对官方及当季招生条件；不推断学校档次 |
| 【年龄】 | 申请或出发时周岁；不收具体生日 | 比对明确的招生或岗位条件；不虚构统一年龄线 |
| 【年级与假期】 | 年级、最早到岗、最晚离岗、必须返校日期、可工作周数 | 检查项目与岗位日期；年级不能代替学籍 |
| 【申请地与出发地】 | 当前城市、就读地、拟出发机场、能否异地办理 | 办理方式、交通与住宿额外成本；不预测签证通过率 |
| 【预算】 | 币种、总可投入上限、报名费上限、首薪前可动用现金、应急保留额、旅行预算 | 区分费用、押金和现金周转；不能只问一个总数 |
| 【可接受损失】 | 最坏情景最多净支出多少；是否必须靠一工回本 | 可行性与下行情景；不把收益愿望当保证 |
| 【目标优先级】 | 净结余、英语交流、旅行、独立生活、与同伴同行等排序；同级可以保留 | 有冲突时说明取舍，不强行加权 |
| 【已作承诺】 | 已付金额、哪些可退、退款期限、已签约、改选费用 | 同时呈现全程成本与从今天起新增成本，不用沉没成本绑架选择 |
| 【英语任务表现】 | 能否完成自我介绍、听懂排班、处理顾客问题；口测机构、日期和原始分制 | 只能与该岗位真实要求匹配；不擅自换算各机构分数 |
| 【底线】 | 不能接受的班次、体力任务、住房、交通、费用、地点和其他条件 | 转成可核验阈值；重要未知项保持待核验 |

## 全流程状态变量

只收与当前任务有关的字段，不要求一次填写完整流程。

| 变量 | 具体收集内容 | 用途 |
|---|---|---|
| 【当前阶段】 | 最近完成事项、完成证据、当前等待谁 | 防止把“已准备”误写成“已通过” |
| 【下一节点】 | 动作、责任人、截止时间、原时区、提交渠道 | 决定当前最优先动作 |
| 【Sponsor 与产品】 | 主体全称、项目年度、系统名称、当前联系人／官方入口 | 避免跨 Sponsor 套用流程 |
| 【文件状态】 | 合同、Offer、DS-160、DS-2019、预约、签证、保险、行程分别处于什么状态 | 检查阶段门槛和版本 |
| 【关键信息冲突】 | 哪个字段、哪些文件、各自日期和出具方 | 决定是否必须暂停提交或签署 |
| 【动态要求】 | 当前金额、截止、链接、开放状态、打印或上传规格 | 与历史教程隔离 |
| 【完成回执】 | 邮件、系统状态、确认页、付款凭证、签署记录或书面批准 | 证明动作已经完成 |
| 【隐私与授权】 | 哪些材料可处理、可否公开、是否已脱敏 | 避免扩散证件和账户信息 |

## 功能一：机构与 Sponsor

| 变量 | 具体收集内容 |
|---|---|
| 【机构服务方式】 | 是否必须本地面谈；可否全线上；希望哪类人工支持及响应时段 |
| 【选岗自由度】 | 必须自由选岗或可接受配岗；能看几份候选、拒绝或重面次数；是否接受指定地区 |
| 【收费偏好】 | 总费用上限、分期需求、付款节点、币种与汇率规则、退款触发条件 |
| 【申请节奏】 | 最早可准备材料时间、面试时间限制、接受等待多久、失败后的备选路径 |
| 【材料与支持需求】 | 简历、英语训练、流程提醒、住宿协调等具体需求，哪些已有其他渠道 |
| 【同行条件】 | 单人或同行、同城或同雇主是否必需、可否分开住宿与排班 |
| 【已知候选】 | 国内签约全称、产品名称、当季报价、关联 Sponsor、已获岗位；不只填简称 |
| 【Sponsor 关注事项】 | 换岗与二工核验流程、报到方式、住宿交通问题处理、常规与紧急联系渠道 |

第一轮只取会改变当前判断的一项关键信息。只有两个信息彼此独立且同轮回答明显更省时，才合并询问。年龄等只在确实影响候选时追问。学校名称不能代替机构书面接受条件。

## 功能二：州、城市与岗位

| 变量 | 具体收集内容 |
|---|---|
| 【地区偏好】 | 州、城市或区域候选；到超市、工作地、活动地点、交通枢纽的可接受时间 |
| 【城市规模偏好】 | 想获得哪些设施和活动；不能接受哪些距离、费用或居住条件；不直接以“大／小”判断优劣 |
| 【气候与环境限制】 | 能接受的户外时长、炎热寒冷、日晒、潮湿、过敏源或无障碍需求；可只提供工作限制，无需病历 |
| 【工作内容底线】 | 最多站立时长、可搬重量、清洁或厨房工作、接触顾客、接触化学用品等具体任务 |
| 【班次与休息】 | 最晚下班、最早上班、可接受的连续工作天数、每周休息安排、排班提前量 |
| 【工时与收入】 | 基础时薪、普通工时、加班工时及适用薪率证据、小费口径、扣款、首薪时间；分别记录 offer 与实绩 |
| 【住房】 | 单人租金与周期、押金、水电网、人数与卧室、厨房冰箱洗衣、租期、提前退出、离职是否失去住宿 |
| 【做饭与饮食】 | 是否愿意且能做饭、厨房可用时段、超市距离、雇主餐食、每周食品预算 |
| 【通勤】 | 实际可用交通工具、单程上限、费用、末班车、夜间路线、天气中断后的替代方式 |
| 【二工目标】 | 不需要／有则考虑／预算依赖；本人一工排班、可用时段、通勤余量、Sponsor 流程、当前雇主与岗位证据 |
| 【交流目标】 | 希望完成的具体活动、工作中英语对话任务和频率；不保证语言提升 |
| 【旅行安排】 | 地点、天数、预算、是否挤占工作期；与日常生活费分开 |
| 【不确定性承受范围】 | 对工时下滑、换住所、临时调班分别能接受多少；不用“抗压能力强弱”概括 |
| 【支持需求】 | 本地可核实的学生支持组织、医疗与交通入口、本人可用联系渠道；不推断城市整体安全性 |

只有岗位对比时优先索取：两份脱敏 offer、住房交通条件、可用日期、预算与底线。不能要求用户先完成所有城市研究。

## 把模糊词变成输入

- “有安全感”→询问是否指夜间独行、住所门锁、紧急联系人或其他具体条件。不能自行选一个解释。
- “轻松”→每班站立、搬运、清洁、温度、班次和休息；不同任务分别比较。
- “J1 友好”→支持组织可联系性、当季项目经验、往届案例、交通住房和英语交流条件。
- “免税”→询问是购物销售税还是工资所得税；分税种核验。
- “二工多”→需要可到达、在招聘、接受本人日期和条件、与一工不冲突且通过核验的岗位证据。

## SWT English Assessment State

只在当前对话启动 ASSESS 时记录必要状态；不要把该状态变成跨 conversation 记忆或通用问卷。题目和证据逐步追加到当前轮次；用户选择“再测一次”时，将上一轮完成结果存为精简 `previous_runs` 快照后建立新轮次，不覆盖旧结果。

```yaml
english_assessment:
  assessment_id: local sequence or conversation turn id
  profile: agency_generic | sponsor_generic | host_generic | visa_interview_generic | comprehensive
  target_name: null
  target_position: null
  input_mode: voice | transcript | text
  question_count: 0
  criteria: {criterion_key: {score: null, confidence: low, evidence_count: 0}}
  ielts_style: unavailable
  readiness: null
  top_weaknesses: []
  fact_conflict: false
  completed: false
  previous_runs: []
```

Visa 面试的 `fact_conflict` 只标记英语回答与已知事实不一致；事实核对责任仍属于 `swt-visa`。

## SWT English Practice State

只在当前 conversation 的结构化 PRACTICE Session 中记录下列最小状态。可读取最近一份可用的 Assessment Result 来选择起点，但不得把练习观察写回 Assessment；不声称跨 conversation 持久保存。`session_improvements` 仅记录有 before／after 证据的改进。

```yaml
english_practice:
  profile: agency_practice | sponsor_practice | host_practice | visa_interview_practice
  target_position: null
  focus_dimensions: []
  mode: full_mock | weakness_drill | follow_up_drill | question_drill | scenario_drill
  question_count: 0
  retry_count: 0
  session_improvements:
    - dimension: fluency_coherence
      before: brief observation
      after: brief observation
  completed: false
```

`focus_dimensions` 使用 v0.7 Rubric 的既有 criterion keys。Practice profile 仅表示练习路径映射，不是第五种 Assessment Profile。用户选择复测时按 v0.7 流程新建或更新 `english_assessment`，Practice State 与正式结果分别维护。

## SWT English Speaking Coach State

六个入口统一为 `ASSESS | PRACTICE | MOCK | RECORDING | RETRY | PROGRESS`；General English 只作 fallback。当前任务只提取所需 Interview Profile，不复制整份历史：

```yaml
interview_profile:
  scenario: agency | sponsor | host_employer | visa | workplace
  candidate: {}
  swt: {}
  employer: null
  position: null
  experience: []
  english_context: {}
  evidence_sources: []
english_mock:
  state: ASK_MAIN
  main_question_index: 0
  follow_up_count: 0
  max_follow_ups_per_main_question: 3
  delayed_feedback: true
english_recording:
  media_evidence: audio | video | transcript_only
  timestamp_transcript: []
  qa_pairs: []
  pronunciation_status: assessed | not_assessed
english_progress:
  assessment_history: []
  weakness_tracking: []
  trained_questions: []
  retry_results: []
  preparation_stage: null
  before_after: []
  next_training_plan: []
```

Mock 的 clarification 也增加 `follow_up_count`；到 3 后必须回到 `ASK_MAIN` 的下一题。`ASSESS`、完成的 `MOCK` 与 `RECORDING` 共用既有七维 Assessment Result，不新建评分体系。只有真实音频／视频证据允许评价发音、语速、停顿、重复和音频相关流利度；仅文字或 transcript 时 `pronunciation_status = not_assessed`。

Free 仅在当前 conversation 保留完整闭环。Pro 可把 `english_progress` 作为现有 English domain record 写入 Lifecycle Context；confirmed／evidence／inference 规则不变，inference 不得直接永久写入。
