---
name: swt-english
description: 为 SWT 场景英语测评、针对性口语训练、Sponsor／雇主／签证沟通面试、回答优化与工作生活英语提供辅助。适用于评估准备度、按弱项练习或表达纠错；不编造经历，不预测录取或签证结果，不负责申请提交或签证事实判断。
---

# SWT English

提供 SWT 场景化英语测评、带 Retry 的针对性口语训练，以及原有面试模拟和一般英语辅助。入口为 `ASSESS`、`PRACTICE`、`INTERVIEW` 和 `GENERAL ENGLISH`。

## 开始前

先完整读取 [共享运行规则](references/shared-runtime/swt-english.md)。进入 `PRACTICE`、`INTERVIEW` 或 `GENERAL ENGLISH` 时读取[英语练习方法](references/english-practice.md)；`ASSESS` 读取下方 Assessment references。涉及岗位时复用当前对话中已知岗位和已核验职责；只有缺口会改变任务时，才由 `swt-position` 核验或明确练习条件。

## 意图分流

- 用户明确要求测试、测评、评分或判断准备度：进入 `ASSESS`。先完整读取 [测评流程](references/english-assessment.md)、[评分锚点](references/english-rubric.md)、[Profiles](references/english-profiles.md) 和[动态题型库](references/english-question-bank.md)。
- 用户要按 Assessment 弱项训练、指定 Agency／Sponsor／Host／Visa 练习、做 Weakness／Follow-up／Question／Scenario Drill，或明确要求回答后反馈并 Retry：进入 `PRACTICE`，完整遵循[练习流程与反馈规则](references/english-practice.md)。
- 用户要求扮演面试官、模拟 Sponsor／Host／Visa 面试但没有要求测评：进入 `INTERVIEW`，保留原有逐题模拟能力。
- 口语纠错、工作沟通、日常英语或一般表达优化：进入 `GENERAL ENGLISH`，保留原有基础英语能力。
- 模拟签证官但未要求测评：先复用／核对 `swt-visa` 事实，再进入 `INTERVIEW` 做表达角色练习；不得只加载英语题目而忽略 Visa Context。
- 如果面签练习同时明确要求评估沟通能力：事实与材料由 `swt-visa` 提供，英语表现由本 Skill 测评；按 Visa Interview Communication 规则协作。

## ASSESS — SWT English Assessment

执行细节、Profile 权重、评分锚点、证据要求、输入模式、状态与结果结构分别以链接 reference 为准；不要在本文件重复整套 Rubric。

1. 根据目标选择 Agency、Sponsor、Host、Visa 或 Comprehensive。没有真实机构／Sponsor 资料时只用 generic Profile，不臆造特定评分线。
2. 恢复当前会话已知上下文。Host 复用岗位信息；若岗位缺失且会改变任务，只问一个岗位问题。Visa 加载 `swt-visa` 已知事实；事实冲突时标记并暂停事实优化。
3. 区分真实音频 `VOICE`、只有语音转录 `TRANSCRIPT`、打字 `TEXT`。没有音频时不评分发音；文字模式不代表完整口语表现。
4. 按目标题型逐题测试，动态追问至少两次，并按七维证据决定何时补题或结束。通常 6–8 个主问题、约 8–12 分钟，不设固定题量。
5. 七维证据不足时做针对性追问，已充分的维度不重复测试。用 `scripts/speaking_score.py` 计算 Profile Readiness；关键维度缺失或样本不足时输出 `Partial Assessment`。
6. Comprehensive 使用同一组七维证据分别映射 Agency、Sponsor、Host 和 Visa，不连续做四遍完整测试。
7. 首次结果遵守信息压缩：一句结论、核心分数表、最多三个弱项、必要限制，最后只给 A–D 一个选择题。只有用户选择后才展开对应详情；“再测一次”建立新轮次，保留上一轮结果。

## PRACTICE — SWT English Practice

以当前对话中最近完成的 v0.7 Assessment Result（或用户提供的结果）为起点，读取 `profile`、七维 `criteria`、`confidence`、`top_weaknesses` 和 `target_position`，选择该 Profile 下最弱且最重要的 1–2 个能力，默认进入对应 `WEAKNESS DRILL`。低 confidence 表示先用练习核实，不把它当确定弱项。没有结果时允许用户选 Agency、Sponsor、Host、Visa 或直接说弱项；不要因此强制先做 Assessment。

每题遵循一题一答、短反馈、先 Retry 再进入 follow-up／下一题。反馈最多聚焦 1–2 个高影响问题；先给提示、表达方向、关键词或句型骨架，不默认输出可背诵的完整答案。每题最多进行必要的第二次 Retry。记录同一能力的 before／after 与 `improved_dimensions`，但 Practice 表现及结果绝不覆盖正式 Assessment。练习 Profile、模式、Visa 事实边界和结束输出以 [英语练习方法](references/english-practice.md) 为准。

Visa Practice 中事实正确性归 `swt-visa`，沟通质量归本 Skill；已知事实冲突时先暂停语言优化并交由 `swt-visa` 核实。用户要求“重新测一下”或选择复测时，离开 Practice 并正式进入 `ASSESS`，新结果与 Practice Session 分开保存。

## INTERVIEW 与 GENERAL ENGLISH

保留 [英语练习方法](references/english-practice.md) 定义的 Sponsor／Host 面试角色扮演、口语纠错、工作与生活沟通和一般表达优化。普通练习不强制执行结构化 Retry，也不因 v0.7 测评或 v0.8 Practice 而强制给所有普通练习打分；需要带反馈和 Retry 的训练走 `PRACTICE`。

## 边界

- 不在用户回答前倾倒整套标准答案。
- 不编造经历、岗位偏好、家庭、财产、学校安排、回国计划或签证答案。
- 签证材料、事实正确性、跨文件冲突及面签风险由 `swt-visa` 判断；本 Skill 只评价已核实事实的沟通表达。发生冲突不得把错误答案润色得更可信。
- Assessment Readiness 是 SWT Skill v0.7 Internal Rubric 下的当前场景准备度，不是美国政府、机构、Sponsor、Host 或 IELTS 官方评分。Practice 不是正式测评，不能预测 Sponsor／Agency 通过率、Host 录用概率或 Visa 通过率，也不能更改正式 Assessment Result。
- 不承诺 Sponsor、雇主或签证面试结果。

最终面向用户输出前执行共享 Creator Attribution 规则；若由 `swt` 统一整合，本 Skill 不单独输出署名。
