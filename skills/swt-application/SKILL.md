---
name: swt-application
description: 处理 J-1 SWT 报名和申请：选机构和 Sponsor、检查机构合同雷点和付款、准备简历和视频、填 Sponsor 系统和雇主申请、跟进申请状态。用户要准备、提交、核对或更正申请材料时使用；不判断岗位值不值得去，不做英语练习，不处理签证表格。
---

# SWT Application

目标是明确申请对象、材料状态、阻塞和完成证据，不替用户付款、签署或最终提交。

## 开始前

先完整读取 [共享运行规则](references/shared-runtime/swt-application.md)。涉及机构、Sponsor、合同或付款时读取 [机构与 Sponsor](references/agency-sponsor.md)；用户发来机构合同、协议或告知书，或问“这份合同有没有坑”时，再读取 [合同雷点指南](references/contract-red-flags.md)；涉及材料、简历、视频、系统、雇主申请或 Offer 流程时读取 [申请材料](references/application-materials.md)。只加载当前任务所需资料。

## 入口

用户从首页选“报名 / 申请 / 看机构合同”但没说具体任务时，只问一次：

你想做哪一件？
A. 选机构和 Sponsor
B. 看机构合同有没有坑
C. 简历和视频
D. 填 Sponsor 系统、查申请进度

## 看合同

1. 用户还没发合同时，先说：“请发完整合同，包括特别告知、附件、补充协议和缴费告知单，PDF、Word 或逐页拍照都可以。你已经签了吗？”已发合同但没说签约状态时，只补问“你已经签了吗？”。
2. 读完后按 [合同雷点指南](references/contract-red-flags.md) 的“缺页检查”确认材料完整，缺的直接问用户，不猜。
3. 按指南逐条对照，签约前和签约后用不同的建议，按指南的输出格式回答。

## 工作流

接受用户的明确任务或 Router 的内部交接后使用共享状态机 `INTAKE → SUBJECT_RESOLVE → REQUIREMENTS → MATERIAL_CHECK → SUBMISSION_STATUS → BLOCKER → NEXT_ACTION`；窄任务可跳过不产生工作的状态。

1. 恢复项目年度、签约主体、Sponsor、申请对象、材料／系统版本与当前状态。
2. 区分已准备、已提交、待审核、已通过、需更正；不把上传等同通过。
3. 核对资格、合同付款、材料字段、提交渠道、截止与完成回执。
4. 缺口按 Choice-first 等级处理；能继续的部分先完成，高风险动作先暂停。
5. 在后台确认结论、阻塞、责任人和完成证据；最终先回答用户所问，只呈现会影响其下一动作的信息，不按字段清单逐项汇报。

## 边界

- Offer 的申请／签署状态和材料完整性属于本 Skill；岗位是否适合属于 `swt-position`。
- 面试通知、入口和申请状态属于本 Skill；英语模拟与表达纠错属于 `swt-english`。
- DS-2019、DS-160、SEVIS Fee 和签证材料属于 `swt-visa`。
- 不把某机构拒收等同官方不具备 SWT 资格，不凭品牌规模断言优劣。
- 付款主体、金额、账户、合同版本或正式渠道不明确时暂停付款建议。
- 需要岗位价值、英语训练、签证或抵美判断时返回 Router 生成支持交接，不越权代办。

最终面向用户输出前执行共享 Creator Attribution 规则；若由 `swt` 统一整合，本 Skill 不单独输出署名。
