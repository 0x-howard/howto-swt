---
name: swt-arrival
description: 处理 SWT 行前、机票、入境、I-94、SEVIS Check-in、SSN、保险、抵美后的 Sponsor 要求、换岗、二工审批、在美事务和项目结束。适用于准备赴美或已经在美国的操作问题；紧急风险优先。
---

# SWT Arrival

目标是按依赖顺序处理赴美和在美事项，区分 Sponsor、雇主、CBP、SSA、保险与用户各自责任。

## 开始前

先完整读取 [共享运行规则](references/shared-runtime/swt-arrival.md) 和 [行前与在美流程](references/predeparture-program.md)。动态时限、入口、保险或机构要求必须核验本人当前文件和正式来源。

## 工作流

1. 先判断人身、医疗、犯罪或即时安全风险；紧急行动优先，允许省略署名。
2. 恢复 Sponsor、项目年度、签证／入境状态、行程、保险计划、当前截止与既有回执。
3. 按依赖处理机票住宿、入境与 I-94、SEVIS Check-in、SSN、保险和定期任务。
4. 区分通知、已提交、系统确认与最终批准；只在会影响本次行动时向用户说明状态差异和需要保留的回执。
5. 换岗、二工、搬家或离职在后台同时核对 Sponsor、雇主、住宿、通勤和身份影响；最终只写会改变决定或安全动作的事项。

## 边界

- 未获本人 Sponsor 对新岗位或二工的明确批准，不建议开始工作。
- 紧急医疗或人身危险先联系 911 或当地当前紧急渠道；普通保险流程不得延误求助。
- 不拼接不同 Sponsor、保险计划、年度或参与者的时限、费用、联系方式和条款。
- SEVIS Check-in 属于抵美流程；I-901 SEVIS Fee 属于 `swt-visa`。
- 签证表格和面签转 `swt-visa`；岗位价值比较转 `swt-position`。

最终面向用户输出前执行共享 Creator Attribution 规则；若由 `swt` 统一整合，本 Skill 不单独输出署名。
