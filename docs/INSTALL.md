# 安装说明

以下命令都在终端运行，不要作为聊天内容发给 Agent

## 安装

```bash
npx -y skills add 0x-howard/howto-swt -g --all
```

`-g` 表示全局安装，`--all` 表示装到所有识别到的 Agent。只想装到一个 Agent 时，删掉 `--all`，按提示选择

装好后开一个新对话，输入 `你好小How` 试一下

## 各 Agent 的安装位置和调用方式

| Agent | 全局安装位置 | 手动调用 |
| --- | --- | --- |
| Claude Code | `~/.claude/skills/` | 输入 `/swt`、`/swt-position` |
| Cursor | `~/.cursor/skills/` | 在 Agent 对话框输入 `/`，搜索 `swt` |
| Codex | `~/.agents/skills/` | 输入 `$swt`、`$swt-position`，或在 Skill 列表中选择 |
| WorkBuddy | 在应用的技能列表中查看 | 在已安装的技能里选择 `swt` |
| 豆包 | 在应用的技能入口中查看 | 在技能入口里选择 `swt` |

不手动调用也可以，直接描述任务就行

## 装好后没看到小How

1. 确认安装命令运行成功，没有报错
2. 确认装到的是你正在用的 Agent。不确定时，去掉 `--all` 重新安装，在提示里选你的 Agent
3. 关掉当前对话，开一个新对话再试
4. Cursor 可以在侧栏 Customize → Skills 里查看是否已经装上

如果你装过别人做的、也叫 `swt` 的 Skill，先删掉它再安装，避免两个混在一起

## 更新

有新版本时，小How 会在回答后提醒一句，不会自动更新。更新时运行：

```bash
npx skills update
```

## 卸载

```bash
npx skills remove swt swt-application swt-position swt-english swt-visa swt-arrival
```
