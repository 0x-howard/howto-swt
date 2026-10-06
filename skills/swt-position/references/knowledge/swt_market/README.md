# SWT Market Knowledge Layer

`swt_market` 是 SWT 地理分布、项目存在规模与 Community Support infrastructure 的背景知识层。

它用于查询 BridgeUSA Summer Work Travel Participants Map 中的 participant count、州与城市记录，以及官方 Community Support Groups 清单中的基础设施记录。它不是 Offer 评价系统、城市推荐榜或收益评分系统。

本知识层主要辅助回答：

1. 某州是否有较明显的 SWT participant presence。
2. 某城市在 BridgeUSA 地图中的 participant count。
3. 某地的 ACTIVE / INITIAL 数据。
4. 某地是否存在官方 Community Support Group 记录，以及该记录的匹配范围。
5. 城市在本州或全国 participant count 中的位置。

`total` 是 BridgeUSA SWT Map participant count 聚合值；目前没有证据证明它等于去重后的年度独立 SWT 参与者人数。引用时应按 methodology 中的口径表述。

真正的 Offer 判断仍需结合 Money、Housing、Living、Mobility、Job、Infra 六个维度。participant count 或 Support Group 记录本身不构成 Offer 推荐结论。

## 文件

- `state_summary.json`：51 条州级聚合记录。
- `city_summary.json`：2465 条城市级聚合记录。详细字段以此文件为准。
- `support_groups.json`：15 条官方 Support Group 清单记录，保留各类匹配状态。
- `STATE_INDEX.md` 与 `CITY_INDEX.md`：供查找使用的索引。
- `source_metadata.json`：清洗数据的来源语义与运行层来源信息。
- `methodology.md`：口径、限制与匹配解释规则。

由 `scripts/build_swt_market.py` 从插件目录外的 `swt-data-source/SWT_MAP_DATA/cleaned/` 生成。该脚本仅读取 cleaned 输入；位置可通过 `HOWTO_SWT_SOURCE_DATA_ROOT` 配置。
