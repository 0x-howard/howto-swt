# HowTo SWT 怎样工作

## 任务怎么分配

```text
说清了任务 → 直接交给对应 Skill
任务不清楚 / 涉及多件事 → swt 先判断阶段 → 交给对应 Skill
```

`swt` 负责导航：判断阶段、选择 Skill、把已知信息传过去。其余 5 个 Skill 各管一件事：

| Skill | 负责 |
| --- | --- |
| `swt-application` | 报名、机构、Sponsor、合同付款、申请材料 |
| `swt-position` | Offer 分析与比较、回本测算 |
| `swt-english` | 英语测评、练习、面试模拟 |
| `swt-visa` | DS-2019、DS-160、SEVIS 费、面签 |
| `swt-arrival` | 行前、入境、SSN、换岗、在美生活 |

Agent 不能直接切换 Skill 时，小How 会告诉你怎么继续。交接规则见 [`shared/handoff-contract.md`](../shared/handoff-contract.md)，各 Skill 的处理步骤见 [`shared/executor-state-machines.md`](../shared/executor-state-machines.md)

## 谁做什么

- **Agent**：联网搜索、读取 PDF 和图片
- **Skill**：规定怎样识别信息、怎样分析、怎样输出
- **Python 脚本**：需要算准的部分，例如收入、税费、回本和汇率取整

## 信息怎么记住

默认只在当前对话里记住。包根目录有扩展时，经用户同意后可保存到用户指定的目录；没有扩展时照常使用

## 英语练习

`swt-english` 有 6 种模式：测评（ASSESS）、练习（PRACTICE）、模拟面试（MOCK）、录音分析（RECORDING）、重答（RETRY）、继续上次（PROGRESS）。模拟面试中途不纠错，结束后统一按 7 个维度评分；练习每题即时反馈再重答。只有真实录音才评价发音

## 文件从哪来

- `shared/`：共享规则
- `references/`：业务资料和各州参考数据
- `scripts/`：计算脚本
- `skills/*/SKILL.md`：各 Skill 的行为规则

`python3 scripts/sync_shared.py` 会把前三项复制到每个 Skill 目录，方便单独安装某个 Skill。复制出来的文件不要手改
