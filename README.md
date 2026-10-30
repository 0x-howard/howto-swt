# HowTo SWT

**面向 J-1 Summer Work Travel 学生的 AI Skills 工具箱**

![版本](https://img.shields.io/badge/Free-v1.4.0-blue) ![语言](https://img.shields.io/badge/语言-中文-green)

作者：Howard · [@哎哟不想上早八啊](#作者与帮助)（全平台同名）

从报名到赴美，SWT 有不少信息需要自己判断。安装后，你可以在自己的 Agent 里直接问申请、岗位、英语、签证或美国生活的问题，带着已有材料一起理清下一步。

[功能展示](#功能展示) · [快速安装](#快速安装) · [使用方法](#使用方法) · [最近更新](#最近更新) · [作者与帮助](#作者与帮助)

## 能力速览

| 工作目标 | 主要入口 | 常见产出 |
|---|---|---|
| 找到当前阶段和下一步 | [`swt`](skills/swt/SKILL.md) | 问题梳理、下一步建议 |
| 处理报名与申请 | [`swt-application`](skills/swt-application/SKILL.md) | 条件核对、申请清单 |
| 看懂岗位与 Offer | [`swt-position`](skills/swt-position/SKILL.md) | 六维分析、回本测算 |
| 练英语与面试 | [`swt-english`](skills/swt-english/SKILL.md) | 提问、反馈、重试 |
| 准备签证 | [`swt-visa`](skills/swt-visa/SKILL.md) | 材料核对、冲突提醒 |
| 准备赴美与在美生活 | [`swt-arrival`](skills/swt-arrival/SKILL.md) | 操作顺序、问题处理 |

## 功能展示

以下是虚构的使用示例，用来展示可能的对话，不代表真实用户记录。具体回答会随你提供的资料变化。

### 01｜SWT 导航 · `swt`

不知道从哪开始，或手上有几个任务需要安排顺序时，可以先找小How。

> **你：** 我已经报名，Sponsor 英语面试下周进行，但还没选岗位。我现在先做什么？
>
> **小How：** 先准备下周的 Sponsor 面试；岗位选择可以接着处理。告诉我面试形式和你最担心的部分，我们从那里开始。

已明确要做的事可以直接说，例如“分析这个岗位”，不必先经过首页。

### 02｜报名申请 · `swt-application`

机构、Sponsor、合同付款或申请材料有问题时，先把已知情况说清楚。

> **你：** 机构让我先交项目费，但合同里没有写清退款条件，我该看什么？
>
> **小How：** 先查看费用明细、退款触发条件、扣款项目和截止时间；请机构提供书面条款。付款前，先把不清楚的部分确认清楚。

### 03｜岗位分析 · `swt-position`

拿到 Offer 后，可以一起看工资、住宿、交通、生活成本、二工和回本。

> **你：** 德州餐厅岗位：时薪 $16，平均每周 32 小时，工作 13 周，住宿每周 $120。帮我看看能不能回本。
>
> **小How：** 会按收入、住宿、生活成本、交通、二工和落地便利六个方面整理 `要素 | Offer 数据 | 分析`；再分别测算在美收入与开销、项目投入与最终收益。工时不等于保证工时，未知税费和生活费用会标明为估算，二工收入不会默认算入。

这是一份单 Offer 预览，默认不展示收益函数图；你可以继续选择调整工时、比较其他岗位、细看生活条件或判断是否值得选。

### 04｜英语训练 · `swt-english`

SWT English 可用于英语口测、Sponsor、雇主或签证面试准备，可以选择正式模拟或逐题练习。

> **你：** 陪我模拟 Sponsor 英语面试，结束后给我反馈，再让我重答薄弱问题。
>
> **小How：** “Why do you want to participate in Summer Work Travel?” 你回答后，我会按面试节奏继续提问；模拟结束再反馈，并陪你重试。

### 05｜签证准备 · `swt-visa`

核对 DS-2019、DS-160、SEVIS Fee 和面签材料时，以本人真实文件为准。

> **你：** 我的 DS-2019 和 DS-160 草稿里的雇主信息不一致，怎么办？
>
> **小How：** 先不要把不一致的信息当成已确认；对照文件版本和出具方，联系 Sponsor 核实，再根据实际情况更正草稿。不要在聊天里发送完整证件号码。

签证事实由 `swt-visa` 核对；需要英语面签练习时，可以继续用 `swt-english`。

### 06｜赴美生活 · `swt-arrival`

入境、SSN、State ID、住房、工作和返程问题，可以按当前进度逐步处理。

> **你：** 刚到美国，Sponsor 要我做 SEVIS Check-in，我还想申请 SSN，先做什么？
>
> **小How：** 先按 Sponsor 指引完成 Check-in，再确认申请 SSN 所需的状态、时间和材料；保留办理记录。如有紧迫期限，先联系 Sponsor 确认。

## 快速安装

**第一步：在终端执行**，不是在 Agent 的聊天框里执行：

```bash
npx -y skills add 0x-howard/howto-swt -g --all
```

安装前先检查目标位置是否已有同名 Skill，避免无意覆盖。也可以把下面的话发给支持终端操作的 Agent：

```text
请先检查我的 Skills 目录里是否已有同名 swt Skill；确认不会覆盖后，在终端安装 0x-howard/howto-swt 的全部 Skill，然后告诉我安装结果。
```

## 使用方法

**第二步：开启新会话，直接说你想做什么：**

```text
你好小How
帮我分析这份 SWT Offer
陪我模拟 Sponsor 英语面试
```

不知道如何提问时，可以先用小How主入口；知道具体任务时，直接提出任务或调用对应 Skill。已经开始的任务，可以在当前对话继续补充材料和追问。

**第三步：按 Agent 查看安装帮助。** [安装说明](docs/INSTALL.md)和[新手入门](docs/新手入门.md)可作为 Codex、Claude Code、WorkBuddy、豆包 Work 等环境的起点。不同宿主的安装方式和交互能力可能不同；仓库已有静态检查及文本降级测试，不能据此认定所有宿主的原生界面均已完成端到端验收。

分享材料前请移除密码、验证码、完整证件号码等不必要的敏感信息。更多说明见[数据与隐私](docs/data-and-privacy.md)。

## 最近更新

v1.4.0 已在 GitHub main，属于当前开发版本；尚未创建正式 Release。

<!-- CHANGELOG_LATEST_START -->
| 版本 | 更新 |
|---|---|
| v1.4.0 | 明确任务直接进入对应 Skill，岗位分析改为六维和两张回本表。 |
| v1.3.0 | 增加岗位收益函数与交互能力。 |
| v1.2.0 | 整理任务协作、上下文和版本提示。 |
| v1.1.1 | 修复小How入口发现并整理首页。 |
| v1.1.0 | 统一 HowTo SWT 品牌和安装标识。 |
<!-- CHANGELOG_LATEST_END -->

[查看完整更新日志](docs/CHANGELOG.md)

## 作者与帮助

HowTo SWT 由 Howard 围绕 SWT 学生在申请、面试和赴美过程中遇到的实际问题整理。GitHub：[`0x-howard`](https://github.com/0x-howard)；@哎哟不想上早八啊（全平台同名）。

遇到问题可以查看[安装说明](docs/INSTALL.md)和[新手入门](docs/新手入门.md)，或在 [GitHub Issues](https://github.com/0x-howard/howto-swt/issues) 反馈。Skill 提供信息整理与决策支持，具体申请、签证和 Sponsor 要求请以本人文件及官方信息为准。
