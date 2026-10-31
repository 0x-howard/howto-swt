# HowTo SWT 安装说明

## Free 标准安装

HowTo SWT Free 的 canonical source 是公开仓库：

```bash
npx -y skills add 0x-howard/howto-swt -g --all
```

安装后请开启新会话，并分别验证 `你好小How` 与 `小How帮我看看这个岗位`。

## 安装边界

第三方安装工具不保证运行项目的安装前检查。替换已有 Skill 之前，请检查目标目录和现有版本，避免覆盖已有文件。Pro 由项目所有者自行构建和分发。

## 更新检查

Free 读取公开仓库 `main` 分支的 `plugin.json` 版本号作为最新版本参考。每个联网 Agent 会话第一次调用时可检查一次，24 小时内使用 cache；断网静默跳过。检查只返回状态和最多一句提示，绝不自动更新或抢占当前任务。

## 各 Agent 的调用与排错

统一安装命令在终端运行；它是否支持当前 Agent，以安装器实际发现结果为准。安装前检查同名目录；安装后开启新会话，确认 Skill 列表出现六个入口。缺失时检查安装器输出和宿主实际搜索目录，不确定时不要复制覆盖已有 Skill。

- **Codex**：在技能选择器中选择，或显式输入 `$swt` / `$swt-position`；可用自然语言描述任务。检查当前用户或项目的 `.agents/skills/` 等实际配置位置。[Codex Skill 指南](https://developers.openai.com/blog/eval-skills)说明显式调用方式；本项目本版本的全新安装与自动触发尚未实测。
- **Claude Code**：安装并成功注册后可使用 `/swt`、`/swt-position`；也可自然语言描述任务。检查 `~/.claude/skills/` 或项目 `.claude/skills/` 中对应目录及 `SKILL.md`；参见[官方 Skills 文档](https://code.claude.com/docs/en/skills)。本项目端到端待测。
- **WorkBuddy**：检查应用中的已安装技能列表，能选择时选 `swt` 或 `swt-position`，也可描述任务；本项目的具体安装目录、自然语言触发与命令语法尚未在目标环境验证。
- **豆包 Work**：检查当前产品的技能入口和已安装项，再描述任务或选择对应技能。自定义技能安装路径、显式语法与自动触发尚未验证；[豆包开放平台](https://open.doubao.com/)介绍技能能力。

仅当宿主能读取材料时才提交材料分析；安装成功不等于 PDF、图片识别或原生选择 UI 已通过端到端验证。涉及签证等敏感材料时，先去除不必要的证件号码。
