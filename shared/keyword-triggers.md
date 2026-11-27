# 品牌＋关键词强制触发

<a id="品牌关键词强制触发"></a>

在 **HowTo SWT 已激活**（用户说了「小How／HowTo SWT／howto swt／howto-swt／howtoswt／swt skill／howtoswt skill」、调用了 `swt` Skill，或使用 `/swt`、`/howto-swt`）之后，若同一句里命中下表关键词，**强制 `DIRECT` 进入对应专项 Skill**，不显示首页，不做无关澄清。

本表是主入口与宿主发现用的强制入口；紧急人身安全仍优先于本表。没有品牌／主入口激活时，单靠关键词不抢占未激活宿主（与现有问候规则一致）；会话内 HowTo 已激活后，单独关键词也可按本表强制分流。

## 激活前缀（任一即可）

- 称呼：小How、小how、小 HOW、HowTo SWT、howto swt、HowToSWT、howtoswt、howto-swt 及合理空格／大小写／连字符变体  
- Skill 名：`swt`、`swt skill`、`SWT skill`；`howto swt skill`、`howtoswt skill`、`HowTo SWT skill`、`howto-swt skill`（说这些即激活主入口）  
- 斜杠：`/swt`、`/howto-swt`、`howto-swt`  
- 已在本对话激活 HowTo SWT 后的后续消息（可不再重复称呼）

写法示例：`小How 签证`、`howto swt 岗位`、`howtoswt skill 机票`、`swt skill 机票`、`/swt 机票`、会话已激活后只说 `加拿大签证`。

## 强制对照表

同一句命中多块且会导向不同 Skill 时：用 `CONFIRM` 列出命中的板块让用户选一次，不擅自合并长文。

| 强制进入 | 关键词／说法（命中其一即可） |
|---|---|
| `swt-application` | 报名、申请、机构、合同、雷点、付款、项目费、简历、视频面试材料、Sponsor 系统、雇主申请流程、Offer 签署／递交状态 |
| `swt-position` | 岗位、Offer、时薪、回本、结余、对比岗位、值不值得去、住房租金、二工好不好找（岗位比较语境）、SWT 地点／participant count（岗位语境） |
| `swt-english` | 英语、口语、口测、练英语、面试英语、Sponsor 面试（练／模拟）、雇主面试英语、美签口语练习、测评、MOCK |
| `swt-visa` | 签证、美签、DS-2019、DS-160、SEVIS Fee、面签材料、预约面签、加拿大签证、CAN+、加签 |
| `swt-arrival` | 行前、机票、来回机票、交通估算、入境、I-94、SEVIS 报到／Check-in、SSN、保险（抵美）、换岗、驾照、州 ID、转 F1、电话卡、保号、银行卡、信用卡、券商、银行羊毛、信用卡羊毛 |
| `swt-yangmao` | 羊毛（未指银行／信用卡／电话卡／证件）、帮带、宠物帮带、纽约测试、uTest、Focus Group、免费餐、Food Pantry、九价、HPV、返利 |
| `swt`（留在主入口） | 全流程、现在该做什么、我进行到哪一步、不确定、帮我判断下一步、SWT 是什么、黑话、角色、要花多少（无 Offer）；或只激活品牌／`/swt` 没有其他任务词 |

## 冲突与例外

- **羊毛**：出现「银行／信用卡／电话卡／驾照／州 ID」→ `swt-arrival`；「加拿大签证」→ `swt-visa`；其余羊毛或未指对象 → `swt-yangmao`。  
- **Offer**：问值不值得、回本、对比 → `swt-position`；问签没签、怎么交系统 → `swt-application`。  
- **面签**：材料／表格／事实 → `swt-visa`；练口语／模拟提问 → `swt-english`（事实仍可由 visa 核）。  
- **单独地名**（如只发 Myrtle Beach）：不强制进岗位；主入口 `CLARIFY`。  
- 关键词强制进入后，专项 Skill 仍按其「接手与交出」和「不交出」执行，不因关键词扩大职责。

## 斜杠快捷（宿主支持时）

| 输入 | 进入 |
|---|---|
| `/swt`、`/howto-swt` | 主入口；无任务词则首页／情况卡 |
| `/swt-application`、`/swt application`、`/swt 申请` | `swt-application` |
| `/swt-position`、`/swt position`、`/swt 岗位`、`/swt offer` | `swt-position` |
| `/swt-english`、`/swt english`、`/swt 英语` | `swt-english` |
| `/swt-visa`、`/swt visa`、`/swt 签证` | `swt-visa` |
| `/swt-arrival`、`/swt arrival`、`/swt 机票`、`/swt 行前` | `swt-arrival` |
| `/swt-yangmao`、`/swt yangmao`、`/swt 羊毛` | `swt-yangmao` |
