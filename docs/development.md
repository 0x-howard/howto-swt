# 开发与验证

以下命令在仓库根目录运行

## 修改规则或脚本后

改了 `shared/`、`references/`、`scripts/` 或 `assets/`，先同步到各 Skill：

```bash
python3 scripts/sync_shared.py
```

## 提交前

```bash
python3 scripts/sync_shared.py --check
python3 tests/test_plugin.py
python3 scripts/validate.py
python3 scripts/audit_public.py
```

四条都通过再提交。自动测试只检查规则和计算，不代表每个 Agent 都能自动调用；改动入口或触发词后，在目标 Agent 里开新对话试一下 `你好小How` 和一个具体任务

## 打包

```bash
python3 scripts/build_release.py --output /path/to/howto-swt.zip
```

需要发行信息时加 `--manifest /path/to/manifest.json`

## 更新市场数据

原始数据放在仓库外的 `../workspace-docs/source-data/swt-data-source/`，也可以用环境变量 `HOWTO_SWT_SOURCE_DATA_ROOT` 指定。步骤见[数据采集说明](../shared/maintenance/data-collection.md)和[数据字典](../shared/maintenance/data-dictionary.md)
