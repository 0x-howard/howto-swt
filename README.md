# HowTo SWT

## 01 Hero

面向 J-1 Summer Work Travel 学生的 AI 任务系统：从申请、岗位与预算，到英语、签证和抵美后的下一步。

**HowTo SWT Free v1.3.0** · Created by Howard

Free 不是试用壳：它能在当前会话内复用上下文并完整完成一个真实 SWT 任务。Pro 管理跨会话的完整 SWT 生命周期；SWT 陪跑营在 Pro 之上增加社群、直播与真人判断／复核／陪跑。

## 02 Agent 安装

标准 Free 安装来自公开 GitHub source：

```bash
npx -y skills add 0x-howard/howto-swt -g --all
```

| Agent | 当前验证状态 | 入口 |
|---|---|---|
| Codex | ✅ 当前 Runtime 能力清单已核对；无 structured picker 的会话自动使用文本 fallback | [安装说明](docs/INSTALL.md) |
| WorkBuddy | ◐ 已核对本机安装 Runtime 的 structured-choice 静态证据；尚未做真实 UI E2E | [安装说明](docs/INSTALL.md) |
| 豆包 Work | ◐ package adapter 与文本 fallback 回归通过；本轮未验证正式 choice/form UI | [安装说明](docs/INSTALL.md) |
| Claude Code | ◐ interaction contract 与文本 fallback 回归通过；本轮未做真实宿主 UI 验收 | [安装说明](docs/INSTALL.md) |

第三方 `skills add` 无法被 HowTo SWT 代码 100% 硬拦截：一般 Agent 依赖安装前的 Agent Preflight Guard；WorkBuddy 和 HowTo SWT CLI 路径使用代码级 Hard Guard。详情见[安装说明](docs/INSTALL.md)。

## 03 Free vs Pro

| 产品 | 正式边界 | 核心价值 |
|---|---|---|
| HowTo SWT Free | 完成一个完整 SWT 任务 | 当前会话上下文、六个领域 Executor、基础安全与签证风险、决策与下一步 |
| HowTo SWT Pro | 管理一个完整 SWT 过程 | Persistent Profile、Lifecycle State、Offer/English/Visa history、Context Builder、Write Back、持续更新 |
| SWT 陪跑营 | Pro + 真人服务 | 社群、直播、真人判断／复核／陪跑 |

OTP、Offline Activation 和 encrypted bundle 是授权基础设施，不是 Pro 的主要用户价值。

## 04 核心能力

- **Orchestrator / Router**（`swt`）：识别阶段与目标，按 `DIRECT / CONFIRM / CLARIFY` 生成统一 Handoff。
- **Application Executor**：机构、Sponsor、申请材料和 Employer Application。
- **Position Executor**：Offer、地点、工资、住宿、交通、预算、风险与决策。
- **English Executor / SWT English**：Assessment、Practice、Retry、Reassessment 与各类面试。
- **Visa Executor**：事实提取、一致性检查、缺失／冲突、风险与下一步。
- **Arrival Executor**：行前、入境、I-94、SSN、保险、工作与返程。

架构详见[HowTo SWT 怎样工作](docs/architecture.md)。

## 05 使用方式

安装后在新会话直接说：

```text
你好小How
小How帮我看看这个岗位
陪我练 Sponsor 面试
帮我核对签证材料
```

明确任务自动进入对应 Executor；多个方向都合理时只给 2–4 个选择；缺少路由所需信息时只问最少关键问题。更新检查在后台 fail-open，永远先完成用户任务，且只提示、不自动安装。

岗位比较使用确定性的收益函数分析工时、税后工资与每周成本；超过 3 个 Offer 时先展示全量结果，再让你最多选择 3 个做曲线与交点比较。宿主没有原生选择或图表能力时，会自动使用编号选择、函数、表格和区间结论，不影响任务完成。

## 06 数据与隐私

- Free 使用当前会话的 ephemeral task context，不宣称自动跨会话保存。
- Pro 的 canonical context 必须写到 package 之外的显式 `USER_DATA_ROOT`；推断不会未经确认持久化。
- Runtime Knowledge、开发源数据和 User Data 分离；Skill package、Git、overlay 与 references 不保存用户长期数据。
- 不要把密码、OTP、session token 或不必要的证件号码交给 Skill。

详见[数据与隐私](docs/data-and-privacy.md)。

## 07 最近 5 个版本

<!-- CHANGELOG_LATEST_START -->
| 版本 | 更新 |
|---|---|
| v1.3.0 | 新增 Offer Return Function、工时区间最优分析与跨 Agent Interaction Capability Layer。 |
| v1.2.0 | 建立 Orchestration、Pro Context 接口边界与 Runtime Lifecycle；Free 新增 24h fail-open 更新检查。 |
| v1.1.1 | 修复“小How / HowTo SWT”显式调用发现，并重做公开首页与安装入口。 |
| v1.1.0 | 统一 HowTo SWT 品牌、目录和安装标识。 |
| v1.0.0 | 明确 Runtime、Source、Test 与 User Data 的边界。 |
<!-- CHANGELOG_LATEST_END -->

[查看完整更新日志 →](docs/CHANGELOG.md)

## 08 Author

HowTo SWT  
作者：Howard  
@哎哟不想上早八啊（全平台同名） · GitHub：[`0x-howard`](https://github.com/0x-howard)
