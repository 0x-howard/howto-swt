# HowTo SWT 怎样工作

HowTo SWT v1.5.0 由彼此分层的任务、上下文和运行系统组成，并在任务系统内提供确定性的 Offer 回本计算与共享交互能力。

## Task System

```text
User → 明确任务 → 对应专业 Skill → Executor State Machine
User → 模糊或跨模块任务 → swt Router → Routing Policy → 内部 Handoff → 专业 Skill
```

用户已经知道要做什么时，直接由对应专业 Skill 执行，不先显示首页，也不要求复制 Prompt。`swt` 只在任务不清楚、阶段不明或涉及多个专业方向时负责理解目标、识别阶段并选择 `DIRECT / CONFIRM / CLARIFY`。宿主可调度时用内部 Handoff 传递已知事实；宿主确实无法调度另一 Skill 时，才把 `HOWTO_SWT_HANDOFF_V1` 作为手动回退。五个 Domain Executor 是 `swt-application`、`swt-position`、`swt-english`、`swt-visa`、`swt-arrival`。它们共同理解 [`shared/handoff-contract.md`](../shared/handoff-contract.md)，各自状态转移见 [`shared/executor-state-machines.md`](../shared/executor-state-machines.md)。

## Context System

```text
当前会话事实 → Context Builder → Router/Handoff → Executor
```

Free 在当前会话内提供完整 task context，跨会话保存默认关闭。包根存在可选扩展时，可在宿主显式提供的包外目录中保存经用户同意的确认事实；扩展不存在或宿主无法访问包根时，Free 照常独立工作。Inference 必须先经用户确认，才能成为事实。

## Runtime System

```text
Skills CLI 安装 → 新会话发现六个 Skill → 可选版本提示（只读，不自动更新）
```

公开安装使用第三方 Skills CLI，安装边界见[安装说明](INSTALL.md)。`swt` 每个联网会话最多检查一次公开版本号，24 小时缓存，断网静默跳过；检查与更新永远分离，不修改已安装文件。

## 真源与生成物

共享规则在 `shared/`，业务参考在根 `references/`，确定性脚本在根 `scripts/`；`scripts/sync_shared.py` 将运行所需内容生成到六个 Skill 目录，供单个 Skill 独立安装。生成文件不得手工编辑。开发测试、构建输入和原始数据不进入 Skill runtime。用户数据不进入 package 或 Git。

## English Speaking System

`swt-english` 使用 `ASSESS / PRACTICE / MOCK / RECORDING / RETRY / PROGRESS` 六入口。Mock 先建立最小 Interview Profile，单题动态追问上限为 3，过程不教学，结束后复用既有七维 Assessment Result；Practice 则即时反馈并进入 Retry。Recording 只有在真实音视频证据存在时才评价发音及音频相关表现。Free 状态限当前 conversation；可选扩展存在时，Progress 复用同一份已同意保存的上下文。
