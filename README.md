# HowTo SWT

![版本](https://img.shields.io/badge/version-1.5.0-2563EB.svg?style=flat-square) ![语言](https://img.shields.io/badge/语言-中文-16A34A.svg?style=flat-square)

## HowTo SWT 是什么

HowTo SWT 是 Howard 为 J-1 Summer Work Travel（SWT）学生制作的中文 AI Skills 工具箱，共 6 个 Skill。安装到 Claude Code、Cursor、Codex、WorkBuddy、豆包等支持 Skills 的 Agent 后，叫一声"小How"就能用。

装好后，你可以让小How：

- 判断你走到了哪一步，下一步先做什么
- 看懂机构合同、付款条款和申请材料
- 分析一份 Offer 的工资、住宿和生活成本，算出多久能回本
- 模拟 Sponsor、雇主和签证面试，练完给反馈
- 核对 DS-2019、DS-160 和面签材料
- 安排入境、SSN、换岗和在美生活

作者：Howard · @哎哟不想上早八啊（全平台同名）

## 快速开始

**第 1 步：安装**

在终端运行：

```bash
npx -y skills add 0x-howard/howto-swt -g --all
```

只装到某一个 Agent，见下文[安装详情](#安装详情)

**第 2 步：叫小How**

开一个新对话，输入：

```text
你好小How
```

已经知道要做什么，直接说：

```text
小How，帮我看看这份 Offer：德州餐厅，时薪 $16，平均每周 32 小时，做 13 周，住宿每周 $120
```

**第 3 步：在同一个对话里继续**

收到结果后，直接补充材料、追问或修改，不用重新开始

## 全部 Skill

不用记 Skill 名字。直接说任务，小How 会交给对应的 Skill

| Skill | 用途 | 可以这样说 |
| --- | --- | --- |
| [`swt`](skills/swt/SKILL.md) | 不知道从哪开始时，判断阶段和下一步 | 我已经报名，下周 Sponsor 面试，还没选岗位，先做什么？ |
| [`swt-application`](skills/swt-application/SKILL.md) | 机构、Sponsor、合同付款和申请材料 | 机构让我先交项目费，合同没写退款条件，我该看什么？ |
| [`swt-position`](skills/swt-position/SKILL.md) | 分析和比较 Offer，算回本 | 帮我比较这两个 Offer，哪个最后剩得多？ |
| [`swt-english`](skills/swt-english/SKILL.md) | 英语测评、口语练习和面试模拟 | 陪我模拟 Sponsor 英语面试，结束后给反馈 |
| [`swt-visa`](skills/swt-visa/SKILL.md) | DS-2019、DS-160、SEVIS 费和面签 | DS-2019 和 DS-160 里的雇主信息不一样，怎么办？ |
| [`swt-arrival`](skills/swt-arrival/SKILL.md) | 行前、入境、SSN、换岗和在美生活 | 刚到美国，要做 SEVIS Check-in，还想办 SSN，先做哪个？ |

提问时附上这些信息，结果会更准确：

- 项目年份、Sponsor 和目前进度
- 完整的 Offer、合同或材料，PDF 和截图都可以
- 你想要的结果，例如判断、比较，还是能直接用的回答

发材料前，先遮住密码、验证码和完整证件号码。见[数据与隐私](docs/data-and-privacy.md)

## 安装详情

以下命令都在终端运行，不要作为聊天内容发给 Agent

```bash
npx -y skills add 0x-howard/howto-swt -g --all
```

`-g` 表示全局安装，`--all` 表示装到所有识别到的 Agent。只想装到一个 Agent 时，删掉 `--all`，按提示选择

想手动指定 Skill 时：

| Agent | 手动调用 |
| --- | --- |
| Claude Code | 输入 `/swt`，或 `/swt-position` 等具体 Skill |
| Cursor | 在 Agent 对话框输入 `/`，搜索 `swt` |
| Codex | 输入 `$swt`、`$swt-position`，或在 Skill 列表中选择 |
| WorkBuddy | 在已安装的技能里选择 `swt` |
| 豆包 | 在技能入口里选择 `swt` |

**装好后没看到小How：** 确认安装命令运行成功，并且装到的是你正在用的 Agent，然后开一个新对话。更多排查方法见[安装说明](docs/INSTALL.md)

## 最近更新

<!-- CHANGELOG_LATEST_START -->
| 版本 | 更新 |
|---|---|
| v1.5.0 | 读取 PDF 和截图里的 Offer，按最新汇率换算人民币，支持更多 Agent。 |
| v1.4.0 | 说清任务就直接开始，岗位分析改为六个方面加两张回本表。 |
| v1.3.0 | 比较多个岗位时，展示工时变化对收入的影响。 |
| v1.2.0 | 多个任务之间自动衔接，已说过的信息不再重复问。 |
| v1.1.1 | 叫"小How"更容易被识别，首页更简洁。 |

<!-- CHANGELOG_LATEST_END -->

[完整更新记录](docs/CHANGELOG.md)

## 更新与帮助

有新版本时，小How 会在回答后提醒一句。更新时在终端运行：

```bash
npx skills update
```

- [新手入门](docs/新手入门.md)
- [安装说明](docs/INSTALL.md)
- [数据与隐私](docs/data-and-privacy.md)
- [提交问题或建议](https://github.com/0x-howard/howto-swt/issues)
- 作者：Howard · GitHub [`0x-howard`](https://github.com/0x-howard) · @哎哟不想上早八啊（全平台同名）

小How 帮你整理信息、做判断。签证和 Sponsor 的具体要求，请看你收到的文件和官方通知
