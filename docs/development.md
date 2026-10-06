# 开发与验证

以下命令从 `howto-swt/` 根目录运行。面向 Agent 的规则和业务资料各自有唯一真源；不要直接改生成文件。

## 同步与校验

```bash
python3 scripts/sync_shared.py
python3 scripts/sync_shared.py --check
python3 scripts/validate.py
```

`shared/` 是共享规则真源，根 `references/` 保存业务资料。同步命令生成根运行时文件以及各 `skills/<name>/` 中供独立安装使用的本地资料、脚本与示例。生成后的包随 Skill 目录安装，不包含测试、数据构建或验证工具。

## Regression tests

```bash
python3 -m unittest discover -s tests/unit -v
python3 -m unittest discover -s tests/integration -v
python3 -m unittest discover -s tests/evals -p 'test_*.py' -v
python3 tests/test_plugin.py
```

自动测试验证文件、路由规则和计算工具的约定，不证明不同 Agent 的真实模型一定会自动激活 Skill。发布后仍应在目标 Agent 的新 conversation 中检查品牌触发和直接任务分流。

## 市场资料更新

构建时源数据位于工作区私有目录 `workspace-docs/source-data/swt-data-source/`。市场资料变更后，使用 `HOWTO_SWT_SOURCE_DATA_ROOT` 指向该目录，并按数据维护说明运行构建与来源校验。安装包不应包含原始下载或清洗中间产物。详见[数据采集维护说明](../shared/maintenance/data-collection.md)和[数据字典](../shared/maintenance/data-dictionary.md)。
