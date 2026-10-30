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

Free 使用仓库根目录的 `runtime-manifest.json` 作为公开 canonical version metadata。每个联网 Agent 会话第一次调用时可检查一次，24 小时内使用 cache；断网静默跳过。检查只返回状态和最多一句提示，绝不自动更新或抢占当前任务。
