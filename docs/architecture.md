# HowTo SWT 怎样工作

HowTo SWT 由六个可独立发现的 Skills 组成。主入口 `swt` 处理显式品牌调用、一般导航和跨模块分流；当用户任务明确时，直接进入最相关的 Specialist。

```text
用户说明情况 → 判断阶段与任务 → 进入对应 SWT Skill → 加载所需资料或计算 → 回答当前问题
```

| Skill | 主要职责 |
|---|---|
| `swt` | 显式品牌入口、导航、风险分流与跨 Skill 协调 |
| `swt-application` | 报名、机构／Sponsor、申请材料与 Employer Application |
| `swt-position` | 岗位、Offer、地点、预算与收益比较 |
| `swt-english` | SWT 英语 Assessment、Practice、Interview 与一般口语 |
| `swt-visa` | J-1 签证材料、事实核对与面签准备 |
| `swt-arrival` | 行前、入境、Sponsor Check-in、工作和返程 |

## 运行与维护文件

安装时每个 `skills/<name>/` 都包含对应的 `SKILL.md` 与它所需的运行资料和脚本。共享规则在 `shared/` 维护，业务参考资料在根 `references/` 维护；`scripts/sync_shared.py` 将它们生成为各 Skill 的本地运行包。Skills CLI 复制单个 Skill 文件夹时，所需内容随包安装。

开发用测试、构建脚本、源数据和本说明文档不属于 Skills CLI 的安装包。实现细节以 [共享架构说明](../shared/architecture.md)、[路由规则](../shared/routing-policy.md)和[结构化决策说明](../shared/decision-model.md)为准。

## 数据来源边界

产品运行只需要随 `swt-position` 安装的规范化地点资料。完整抓取和清洗源数据位于产品目录之外；用户数据不会作为项目知识或测试数据写进 Skill 包。隐私和可选持久化规则见[数据与隐私](data-and-privacy.md)。
