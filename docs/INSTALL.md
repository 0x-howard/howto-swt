# 安装说明

以下命令都在终端运行，不要作为聊天内容发给 Agent

## 安装

```bash
npx -y skills add 0x-howard/howto-swt -g --all
```

`-g` 表示全局安装，`--all` 表示装到所有识别到的 Agent。只想装到一个 Agent 时，删掉 `--all`，按提示选择

装好后开一个新对话，输入 `你好小How` 试一下

安装前电脑上需要有 Node.js（用来运行 `npx`）和 Python 3（小How 算收入、回本时要用）

## Windows 用户

- 在 PowerShell 里运行上面的安装命令
- 从 [python.org](https://www.python.org/downloads/) 安装 Python，安装时勾选 “Add python.exe to PATH”
- 装好后在 PowerShell 输入 `python --version`，能看到版本号就说明可以用了

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

有新版本时，小How 会在回答最后提醒一句，例如：

> 🔔 HowTo SWT v1.6.0：xxx 回复 1，我现在帮你更新。

回复 `1`，或随时对小How说“更新小How”，它会帮你运行更新命令。Agent 弹出权限窗口时，选择允许即可。更新后开一个新对话

也可以自己在终端运行：

```bash
npx -y skills add 0x-howard/howto-swt -g --all
```

Pro 版不走这个更新，新版本由 Howard 发新的安装包

## 卸载

```bash
npx skills remove swt swt-application swt-position swt-english swt-visa swt-arrival
```
