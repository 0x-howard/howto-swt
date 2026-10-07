# HowTo SWT 安装说明

## Free 标准安装

HowTo SWT Free 的 canonical source 是公开仓库：

```bash
npx -y skills add 0x-howard/howto-swt -g --all
```

安装后请开启新会话，并分别验证 `你好小How` 与 `小How帮我看看这个岗位`。

## Runtime 与 Edition

受控安装的 canonical package 路径为 `<skills-root>/howto-swt`；WorkBuddy 使用 `~/.workbuddy/skills/` 下的 flat-six 布局。CLI 写入 `.howto-runtime.json`，只用明确的 `edition: free|pro` 判断 Edition，不读取六个 Skill 的内容猜测。

如果目标 Edition 与已安装 Edition 不同，CLI 返回 `EDITION_REPLACE_CONFIRMATION_REQUIRED`，并带上 installed edition/version 与 target edition。最初的“安装 Free/Pro”不等于替换确认；只有用户再次明确确认，installer 才能 stage、validate、backup、replace、verify，失败时 rollback。

## 第三方 Installer 边界

`npx skills add ...` 是第三方 CLI。HowTo SWT 无法保证它在写文件前执行本项目代码，因此不能声称所有第三方安装路径都有代码级 Edition Guard：

- 一般 Agent：先读取现有 Runtime Identity 并执行 Agent Preflight Guard；发现不同 Edition 时停止并向用户确认。
- WorkBuddy：使用 HowTo SWT CLI adapter，在 `~/.workbuddy/skills/` 执行代码级 Hard Guard 与六目录原子替换。
- Pro：始终使用公开 [HowTo SWT CLI](https://github.com/0x-howard/howto-swt-cli) 完成授权安装／更新。

## 更新检查

Free 使用仓库根目录的 `runtime-manifest.json` 作为公开 canonical version metadata。每个联网 Agent 会话第一次调用时可检查一次，24 小时内使用 cache；断网静默跳过。检查只返回状态和最多一句提示，绝不自动更新或抢占当前任务。

Pro 复用 `howto check-update howto-swt-pro --auto --json`。会员更新权限到期后，已安装版本仍可继续使用，但不能取得新版本。
