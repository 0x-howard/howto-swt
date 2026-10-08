# HowTo SWT 怎样工作

HowTo SWT v1.3.0 由三个彼此分层的系统组成，并在 Task System 内增加确定性 Offer Return 与共享 Interaction Capability Layer。

## Task System

```text
User → Router → Routing Policy → Handoff Prompt → STOP
     → User confirms/modifies/resends → Domain Executor → Executor State Machine
```

`swt` 只负责理解目标、识别阶段、选择 Executor、整理上下文并决定 `DIRECT / CONFIRM / CLARIFY`。它生成完整、可直接发送的 Handoff Prompt 后必须停止；用户确认、修改或重新发送后，Executor 才开始。五个 Domain Executor 是 `swt-application`、`swt-position`、`swt-english`、`swt-visa`、`swt-arrival`。它们共同理解 [`shared/handoff-contract.md`](../shared/handoff-contract.md)，各自状态转移见 [`shared/executor-state-machines.md`](../shared/executor-state-machines.md)。

## Context System

```text
Persistent State → Context Builder → Router/Handoff → Executor → Write Back
```

Free 在当前会话内提供完整 task context。Pro 在 package 外管理 canonical Profile、SWT Case、Lifecycle、Domain Records 与 Events，并只向当前 Executor 提供相关切片。Confirmed Fact 与 Evidence Fact 可以写回；Inference 必须先成为 temporary hypothesis，再经用户确认。

## Runtime System

```text
Runtime Identity → Edition Guard → Update Check → Stage → Validate → Backup
→ Replace → Verify → Cleanup | Rollback
```

公开 CLI 管理 `.howto-runtime.json`、相同 Edition 升级、跨 Edition 二次确认、WorkBuddy flat-six 安装与失败回滚。Update Check 与 Apply 永远分离；Free 的第三方 Skills CLI 安装边界见[安装说明](INSTALL.md)。

## 真源与生成物

共享规则在 `shared/`，业务参考在根 `references/`；`scripts/sync_shared.py` 将运行所需真源同步到六个 Skill。开发测试、构建输入和原始数据不进入 Skill runtime。用户数据不进入 package、Git、overlay 或 references。

## English Speaking System

`swt-english` 使用 `ASSESS / PRACTICE / MOCK / RECORDING / RETRY / PROGRESS` 六入口。Mock 先建立最小 Interview Profile，单题动态追问上限为 3，过程不教学，结束后复用既有七维 Assessment Result；Practice 则即时反馈并进入 Retry。Recording 只有在真实音视频证据存在时才评价发音及音频相关表现。Free 状态限当前 conversation，Pro Progress 复用既有 Lifecycle Context。
