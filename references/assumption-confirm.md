# 测算前确认假设（交互式用户提问）

学生通常先丢 **Offer PDF／截图**。读完材料后**必须触发宿主的交互式用户提问**（Cursor：`AskQuestion`；WorkBuddy 等：`AskUserQuestion`／同类），让用户点选项，不要只用聊天里的 Markdown `1. 2.` 冒充。

## 交付优先级（硬规则）

1. **当前会话若暴露 `AskQuestion`／`AskUserQuestion`／`request_user_input` 等交互提问工具**：必须调用它出选项；禁止只贴编号列表当最终交互。  
2. **否则若宿主声明支持原生 `single_choice`／`structured_form`**：走 Interaction Layer 的 `delivery: native`。  
3. **两者都没有**：才允许脚本 Markdown 表 + 编号选项作 fallback，并在内部记下「无交互提问工具」。

`budget.py` 返回 `stage: confirm_assumptions` 且 `interaction.prefer_native_popup: true` 时，宿主按上面顺序执行，**不能**跳过第 1、2 步直接 Markdown。

## 何时触发

`position_overview` 同时满足时返回 `confirm_assumptions`：

1. 已有时薪（没有时薪才用 `ask_missing` 硬拦）；且  
2. 已收窄到 ≤3 份岗位；且  
3. 没有 `"assumptions_confirmed": true`

## AskQuestion 怎么问（推荐一题）

- **title**：`岗位测算前确认`（或多岗位时带岗位名）  
- **prompt**：用一两句概括「已从材料读到」的关键数 + 「默认／估」将用哪些值（项目费、工时未写则 32h 等）。  
- **options**（单选，推荐项在前）：  
  1. `按上表直接测算`（推荐）  
  2. `我要改数字`（选后下一轮用自由文本或再开一题收集改项）  
- 可选第三项：`先不测算`（取消）

表格式明细可作 AskQuestion 的说明文字，或在选项上方的短摘要里；**主交互必须是可点选项**。

## 弹窗／提问里要覆盖的数

| 分区 | 内容 |
|---|---|
| **已从材料读到** | 时薪、工时（若有）、日期算出的周数、周租等 |
| **默认／估** | 项目费（未给时）、餐／交通／其他；工时材料未写时预填 **32h** |
| **材料未写** | 小费、餐、押金、二工、SSN 等软缺口，一句话带过即可 |

## 用户怎么回

- 选「按上表直接测算」→ 接受表内值，加 `"assumptions_confirmed": true`（缺工时时写入 `hours_per_week: 32`）再跑。  
- 选「我要改数字」→ 下一轮收集改项后再确认。  
- 同轮已写明数字并说「直接算」→ 可一次带上确认标记，不必再问。
