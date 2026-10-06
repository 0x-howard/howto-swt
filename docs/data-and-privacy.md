# 数据与隐私

HowTo SWT 区分三类资料：供 Skill 任务读取的运行时知识、仅供维护使用的开发源数据，以及用户自己的项目资料。

- 安装包只带任务需要的规范化运行资料；完整来源快照和清洗中间数据保存在工作区私有目录 `workspace-docs/source-data/swt-data-source/`。
- 用户发来的个人资料不会作为产品知识或测试样本写进 Skill Repository。
- 跨 conversation 保存默认关闭。只有宿主提供独立的外部目录、用户明确要求保存且运行环境实际调用对应适配器时，才可能使用持久化；否则只依赖当前 conversation。
- 不要把密码、验证码或不必要的证件号码提供给 Skill。签证资料以本人当前文件为准。

完整的数据字段、边界和持久化条件由[状态 Schema](../shared/state-schema.md)、[持久化契约](../shared/persistence-contract.md)和 [user-state schema](../references/user-state.schema.json)维护；本文仅作用户说明，不替代这些真源。
