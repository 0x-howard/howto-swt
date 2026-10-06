# HowTo SWT

面向 J-1 Summer Work Travel 学生的 AI 决策、申请、岗位、英语、签证与赴美辅助工具。

**HowTo SWT Free v1.1.1** · Created by Howard

## 🚀 安装 HowTo SWT

先确认你正在使用的 Agent，再打开统一安装入口：[《HowTo SWT 安装说明》](docs/INSTALL.md)。

| Agent | Free | Pro | 安装方式 |
|---|---|---|---|
| Codex | ◐ 包结构与调用规则已验证 | ✅ Online 安装、更新与 Runtime 已验证 | [安装说明](docs/INSTALL.md) |
| 豆包 Work | 🧪 待完整验证 | ◐ Offline Activation 安装链路已验证；Runtime 待完整验证 | [安装说明](docs/INSTALL.md) |
| Claude Code | ◐ 兼容 Skills CLI；待真实 Runtime 验收 | 🧪 已有适配器，待完整验证 | [安装说明](docs/INSTALL.md) |
| WorkBuddy | 🧪 待完整验证 | 🧪 已有适配器，待完整验证 | [安装说明](docs/INSTALL.md) |

状态只代表现有测试记录，不代表所有宿主版本都已完整验收。

## Free 与 Pro

| 能力 | HowTo SWT Free | HowTo SWT Pro |
|---|---|---|
| SWT 全流程导航 | ✅ | ✅ |
| 报名与申请 | ✅ | ✅ 基于同一 Free 能力基座 |
| 岗位 / Offer 分析 | ✅ | ✅ 基于同一 Free 能力基座 |
| 收入与回本测算 | ✅ | ✅ |
| SWT English | ✅ 基础测评、训练与面试 | ✅ 当前与 Free 共用能力基座 |
| Visa / Arrival | ✅ | ✅ |
| 最新 SWT 知识与规则更新 | 基础维护 | ✅ 会员更新机制 |
| Pro 专属工作流 | — | ✅ 授权安装、更新与 Offline Activation |
| 受限网络 Agent 适配 | — | ✅ Offline Activation 安装链路 |
| 持续版本更新 | 基础维护 | ✅ 会员有效期内获取新版本 |
| 真人陪跑支持 | — | ✅ 陪跑营会员 |
| 获取方式 | 免费使用 | 加入 SWT 陪跑营，登记会员邮箱后开通 |

## 核心能力

- **SWT 全流程 / 下一步**（`swt`）：判断当前阶段、下一步和关键提醒。
- **报名与申请**（`swt-application`）：机构、Sponsor、材料和雇主申请辅助。
- **岗位 / Offer / 预算**（`swt-position`）：比较工资、住宿、交通、生活成本和预计结余。
- **英语测评 / 练习 / 面试**（`swt-english`）：测评弱项并练习 Agency、Sponsor、Host 和 Visa 场景。
- **Visa**（`swt-visa`）：核对 DS-2019、DS-160、SEVIS、预约与面签材料的一致性。
- **Arrival / U.S. Life**（`swt-arrival`）：行前、入境、I-94、SSN、保险、工作与返程事项。

## 使用方式

安装完成后直接用自然语言开始，例如：

```text
你好小How
帮我看看我现在到哪一步了
小How帮我分析这个 Offer
陪我练 Sponsor 面试
帮我核对签证材料
```

## 数据与隐私

- Runtime Knowledge 与 User Data 分离。
- Skill package 不应存储用户敏感个人资料。
- `USER_DATA_ROOT` 是由外部宿主明确配置的可选能力。
- 普通 Skill runtime 不被宣称会自动跨会话保存用户数据。

详见[数据与隐私](docs/data-and-privacy.md)。

## 最近更新

<!-- CHANGELOG_LATEST_START -->
| 版本 | 更新 |
|---|---|
| v1.1.1 | 修复“小How / HowTo SWT”显式调用发现，并重做公开首页与安装入口。 |
| v1.1.0 | 统一 HowTo SWT 品牌、目录和安装标识。 |
| v1.0.0 | 明确 Runtime、Source、Test 与 User Data 的边界。 |
| v0.9.0 | 建立六个 Skills 的结构化决策与任务路由。 |
| v0.8.0 | 增加 SWT English 场景训练、重答与复测闭环。 |
<!-- CHANGELOG_LATEST_END -->

[查看完整更新日志 →](docs/CHANGELOG.md)

## Author

HowTo SWT  
作者：Howard  
@哎哟不想上早八啊（全平台同名） · GitHub：[`0x-howard`](https://github.com/0x-howard)
