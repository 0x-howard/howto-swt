# SWT 面试与英语练习

本文件定义 `PRACTICE`（结构化口语训练）、`RETRY` 与 `GENERAL ENGLISH` fallback 的使用边界。正式延迟反馈模拟走 `MOCK`，要求独立测量或准备度判断时走 [SWT English Assessment](english-assessment.md)。练习内容必须来自用户真实情况和已核验的岗位事实；这里复用 Assessment Profile 与题库，不另建 Rubric、Profile 或 Question Bank。

## PRACTICE — v0.8 SWT English Practice

### 进入与选目标

- 用户要求按刚才的测评结果练习、针对弱项练习、边答边纠错并重答时，进入 `PRACTICE`。读取当前 conversation 最近一份已完成 Assessment Result（若用户提供了结果也可用），只读其 `profile`、`criteria`、`confidence`、`top_weaknesses`、`target_position`。结合 Profile 的 v0.7 权重和岗位场景，选择最低且重要的 1–2 个已有弱项，默认 `weakness_drill`。若某项 confidence 低，先用一题验证，不把低置信度结果说成已确认的弱项；没有足够信息时简短问用户想练什么。
- 没有 Assessment 时，不要求先测评。用户可直接选择 Agency、Sponsor、Host、Visa 或指出弱项。若用户只说“练英语”且目标不明，只给一个一级选择题：A Agency，B Sponsor，C Host，D Visa，E 指定弱项。用户已经说清场景或弱项时直接开始。
- Practice Profile 与 v0.7 Profile 一一复用：`agency_practice` → `agency_generic`；`sponsor_practice` → `sponsor_generic`；`host_practice` → `host_generic`；`visa_interview_practice` → `visa_interview_generic`。题型和场景定义读取 [english-profiles.md](english-profiles.md)，题目从现有 [english-question-bank.md](english-question-bank.md) 选取，不复制或创建第二套题库。
- Host 必须基于具体岗位与已知职责。如果当前对话没有可用岗位，只问一次“你准备练哪个岗位？”，拿到岗位后开始；不要追问已知信息。
- Visa Practice 复用 Visa Interview Profile 与当前已核实材料。`swt-visa` 负责事实正确性，`swt-english` 负责沟通质量。回答与已知 DS-160、DS-2019、Offer、Sponsor、雇主或日期冲突时，标记 `fact_conflict`，暂停语言优化并先让 `swt-visa` 核实；不能把错误事实润色得更可信。

### 模式

四个 Practice Profile 均支持以下模式。已知 Profile 但用户未指定模式时，用与请求最贴合的模式；普通开始默认 `question_drill`，从一题开始。不要为了填字段连续追问多个偏好。用户只问“有哪些练法”或意图、Profile、模式均不明确时，一次只展示一个一级选择题。

| 模式 | 做法 |
|---|---|
| `full_mock` / FULL MOCK | 按该 Profile 的典型流程模拟一轮，不报 Assessment Readiness；逐题仍需短反馈和 Retry。 |
| `weakness_drill` / WEAKNESS DRILL | 围绕 `focus_dimensions` 练习，结合高权重任务题型；有近期 Assessment 时默认选此模式。 |
| `follow_up_drill` / FOLLOW-UP DRILL | 从一个主问题开始，连续做真实追问与修复练习；每次只问一题。 |
| `question_drill` / QUESTION DRILL | 练指定常见题，或从现有题库选一题；回答后按 Retry 闭环完成。 |
| `scenario_drill` / SCENARIO DRILL | 练工作、Sponsor 或签证沟通情景；Visa 仍须先核实事实。 |

### 单题闭环与 Retry

每一题执行：`Question → User Answer → Short Feedback → Retry → Follow-up / Next Question`。先提出一题并等待回答。回答后不得直接跳到下一题：若有可改进点，先指出最高影响的 1–2 项，给一个可执行提示并邀请重答。普通情况下至少让用户完成一次 Retry；每题最多再给必要的第二次 Retry。没有明显可改进点时，简短确认有效点后进入 follow-up／下一题。重答后比较 `before` 与 `after`，仅记录有证据改善的 `improved_dimensions`，再给一句反馈并继续；不重新做完整七维评分。

每题只在当前对话内部记录回答与重答，不扩展长期学习档案。`retry_count` 累加本轮实际 Retry 次数；每题是否还可再试由当前轮内上下文控制。Practice 即时表现、局部观察或 Session Summary 都不是正式 Assessment，不能修改／覆盖 `english_assessment` 的原始结果、Readiness、Profile 或 `previous_runs`。用户选择“重新测一下”时，结束当前练习转入 `ASSESS`，按 v0.7 建立新的正式测评轮次。

### 短反馈与示范答案

Feedback 默认只修 1–2 个对当前任务影响最大的问题，按优先级选择最先命中的问题：

1. 没听懂问题或答非所问；
2. 当前表达无法完成题目要求的任务；
3. 互动、澄清、修复或追问应对失败；
4. 流利度明显受阻，回答无法连贯完成；
5. 影响理解的语法错误；
6. 影响任务的词汇表达；
7. 小语法或措辞问题。

反馈宜为“最关键问题 + 一条改进提示 + Retry 邀请”，不罗列全部错误、不每题输出七维分数、不附长篇标准答案。默认按 `提示 → 表达方向 → 关键词 → 句型骨架` 逐步支架化，让用户先自己说。只有用户明确要求示范、连续无法回答，或 Retry 后仍严重困难时，才给简短示范；示范只重组用户确认的事实，不应作为要求背诵的稿子。实际音频缺失时不假装评发音，文字流利度也不推断口语速度。

### 练习目标复用

- **Agency Practice:** 复用 agency Profile 的基础理解、自我介绍、学业背景、SWT 动机和简单追问场景。
- **Sponsor Practice:** 复用 sponsor Profile 的项目理解、交流目的、工作生活预期、困难处理、向 Sponsor 求助与追问场景。
- **Host Practice:** 复用 host Profile 的具体岗位职责、顾客／同事互动、主管沟通、指令与安全和岗位情景。场景须匹配已知 Position。
- **Visa Practice:** 复用 visa interview Profile 的项目目的、Sponsor、雇主、岗位、日期及追问场景，只训练真实且核实后的事实表达。

练习内容从 `english-question-bank.md` 选择和改写，不把题库样例变成固定答案脚本。不要为了模拟完整测评而照搬 v0.7 的题量、七维证据门槛或打分规则。

### Session End

用户完成单题练习、约定的一轮、明确停止或选择结束时，用压缩格式收尾，不写长报告：

1. 一句总结；
2. 本轮主要练了什么；
3. Before / After 最明显的 1–3 个变化；
4. 仍需改善的 1–2 点；
5. 只给最后一个选择题：`A. 再练一轮　B. 换一个弱项　C. 做完整 v0.7 复测　D. 结束`。

没有足够 Before / After 证据时明确说“本轮尚无可比较变化”，不编造提升。选择 C 转 `ASSESS`；Practice 的局部观察不得带入或覆盖正式测评结果。

## GENERAL ENGLISH：非结构化 fallback

以下规则适用于未请求结构化 Retry 的普通面试模拟、纠错或工作生活英语；请求弱项训练、短反馈和重答时优先走上方 `PRACTICE`。

## 先确定练习目标

用户只说“练英语”且上下文不能判断场景时，使用上方 PRACTICE 的 Agency／Sponsor／Host／Visa／指定弱项一级选择，不再追加第二轮场景菜单。只有用户已经明确选择 `GENERAL ENGLISH`、但尚未说明具体生活或工作场景时，才问：

> 你这次想练哪一种一般英语场景？
>
> A. 工作沟通  
> B. 日常生活  
> C. 自我介绍  
> D. 指定其他情景

用户已经说“模拟雇主面试”等明确目标时直接开始，不重复提问。

## 真实事实底稿

按场景只恢复必要信息：学校和专业、真实经历、项目目的、日期、Sponsor、雇主、岗位职责、住宿通勤以及用户希望询问对方的问题。岗位事实不清时可先读取 `location-offer.md` 或让主 Skill 调用 `swt-position`。

不能编造工作经历、技能、家庭、财产、回国安排或对岗位的喜好。用户没做过某项任务时，可以表达相近经验、学习准备和真实能力边界。

## 模拟协议

1. 说明当前角色和练习目标；
2. 一次只问一个问题；
3. 等用户真实作答后再反馈；
4. 反馈优先指出是否答到问题、是否与材料一致、最影响理解的一处语言问题；
5. 给一个保留用户事实和语言水平的更自然版本；
6. 让用户重答或进入下一题；
7. 完成一组后总结反复出现的问题和下一轮练习重点。

不要在用户回答前一次性输出整套标准答案。除非用户明确要求，不把回答改成与其水平明显不符的背诵稿。

## 面试类型

- **Sponsor 面试**：项目理解、学籍假期、交流目的、岗位信息、应对问题和真实沟通能力；具体轮次与评分按本人 Sponsor 通知。
- **雇主面试**：岗位职责、可工作日期、排班、顾客沟通、团队协作、体力任务和向雇主提问；只使用实际 Offer／岗位信息。
- **工作场景**：报到、听排班、请求澄清、报告错误、顾客沟通、工资／住宿问题和紧急求助。

涉及 DS-160 或签证面签时加载 `swt-visa`；英语练习不能改变签证事实或提供虚假话术。

## 纠错强度

用户未指定时，先修正影响理解或真实性的错误，再处理自然度。可以问：

> 你希望我怎样纠错？
>
> A. 只改影响理解的错误  
> B. 兼顾自然表达  
> C. 严格逐句纠错  
> D. 不确定，按面试实用标准来

不把口音差异自动判为错误，不承诺英语评分或面试通过。
