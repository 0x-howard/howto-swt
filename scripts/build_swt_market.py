#!/usr/bin/env python3
"""Build the SWT market knowledge layer from validated cleaned aggregates."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any
from paths import PLUGIN_ROOT, SWT_MAP_SOURCE_ROOT


SKILL_ROOT = PLUGIN_ROOT
CLEANED_ROOT = SWT_MAP_SOURCE_ROOT / "cleaned"
OUTPUT_ROOT = SKILL_ROOT / "references" / "knowledge" / "swt_market"

STATE_FIELDS = (
    "state",
    "state_code",
    "active",
    "initial",
    "total",
    "city_count",
    "point_count",
    "top_city_record",
    "top_city_record_total",
    "active_share",
    "national_rank_by_total",
    "support_group_record_count",
    "source_name",
    "dataset_last_refresh",
    "retrieved_at",
)

CITY_FIELDS = (
    "state",
    "state_code",
    "city",
    "city_raw_variants",
    "location_type",
    "active",
    "initial",
    "total",
    "point_count",
    "representative_latitude",
    "representative_longitude",
    "active_share",
    "national_rank_by_total",
    "state_rank_by_total",
    "has_support_group",
    "support_group_name",
    "support_group_url",
    "support_group_match_type",
    "source_name",
    "dataset_last_refresh",
    "retrieved_at",
)

SUPPORT_GROUP_FIELDS = (
    "location_raw",
    "support_group_name",
    "website",
    "website_label_raw",
    "state",
    "state_code",
    "location_normalized",
    "location_scope",
    "matched_city",
    "match_type",
    "match_confidence",
)

EXPECTED_COUNTS = {"state": 51, "city": 2465, "support_group": 15}
PARTICIPANT_FIELDS = ("active", "initial", "total")

README = """# SWT Market Knowledge Layer

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
"""

METHODOLOGY = """# SWT Market Data Methodology

## 数据来源

- 数据来源：BridgeUSA Summer Work Travel Participants Map
- 发布机构：U.S. Department of State
- participant count 来源：BridgeUSA SWTDashboard Power BI 查询返回值
- Community Support Group 记录来源：官方 Community Support Groups 清单，经 cleaned 层保留的记录与匹配字段
- 运行层输入：插件目录外 `swt-data-source/SWT_MAP_DATA/cleaned/` 中的州级 JSON、城市级 JSON、Support Groups CSV 和 source metadata

具体 source URL、数据集刷新时间、抓取时间及原始字段定义见 `source_metadata.json`。本知识层只投影已验收的 cleaned 聚合字段，不重新清洗、不重新分组、不修复 manual_review 项。

## participant count

`active`、`initial` 和 `total` 均来自 BridgeUSA Power BI 查询返回的 participant count。`total` 保留 cleaned 输入中的聚合值。

目前没有证据证明 `total` 等同于去重后的年度独立 SWT 参与者人数。因此 Skill 应优先表述为：

- BridgeUSA SWT Map participant count
- BridgeUSA 地图参与者计数
- 当前官方地图中的 SWT presence / participant count

不要表述为：

- 该城市每年有 X 个 SWT 学生
- 该州有 X 个唯一参与者

除非未来获得独立验证。

## 州与城市排名字段

`top_city_record` 只表示该州当前数据中 participant count 最大的 city record。它不表示最热门、最推荐、工作机会最多或收入最高。

`national_rank_by_total` 与 `state_rank_by_total` 仅表示 cleaned 数据中 participant count 的排序位置，不构成质量或推荐评分。

## Support Group 记录数量

`support_group_record_count` 只表示该州在官方 Community Support Groups 清单中的记录数量。该数值不表示成功覆盖的城市数，也不表示服务质量或实际可用性。

## Support Group 匹配

- `exact`：可以视为明确城市匹配。
- `multi_city`、`regional`、`county_or_region`、`affiliate`：只能作为区域性基础设施证据，不能据此断言某一单独城市一定有该组织。
- `unmatched`：不得强制绑定某城市。

保留 cleaned 输入中的所有类型与匹配状态，不对 `manual_review` 中的问题做自动修复或重新绑定。当前需特别保持：

- `Door County, WI`：`county_or_region` / `unmatched`。
- `Door County Affiliate, WI`：`affiliate` / `unmatched`。
- `Bethany Beach and Fenwick Beach, DE`：`multi_city` / `low`，只保留 cleaned 中的部分匹配。
- `Cape Cod Affiliate - Dennis, Not West Yarmouth, MA`：`affiliate` / `regional` / `low`。

## 字段与范围

州级与城市级 summary 保留 cleaned 输入提供的 participant count、记录数、地理字段、排名和来源时间字段。字段值不在本层重新计算。`city_summary.json` 中的 `total` 表示 BridgeUSA SWT Map participant count 聚合值，不表示年度唯一参与者人数。

本层不包含 3649 条原始点位，也不复制 raw Power BI JSON。其数据范围限于州级、城市级聚合与 Support Group 清单记录。
"""


def read_json_records(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
        raise ValueError(f"Expected a JSON object with a data list: {path}")
    return payload, payload["data"]


def project(records: list[dict[str, Any]], fields: tuple[str, ...]) -> list[dict[str, Any]]:
    return [{field: row[field] for field in fields} for row in records]


def participant_totals(records: list[dict[str, Any]]) -> dict[str, int | float]:
    return {field: sum(row[field] for row in records) for field in PARTICIPANT_FIELDS}


def write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def markdown_cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def build_state_index(states: list[dict[str, Any]]) -> str:
    lines = [
        "# SWT Market State Index",
        "",
        "| State | Code | Participant Count | City Records | Top City Record | Support Group Records |",
        "| --- | --- | ---: | ---: | --- | ---: |",
    ]
    for row in states:
        lines.append(
            "| "
            + " | ".join(
                markdown_cell(row[field])
                for field in (
                    "state",
                    "state_code",
                    "total",
                    "city_count",
                    "top_city_record",
                    "support_group_record_count",
                )
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def build_city_index(states: list[dict[str, Any]], cities: list[dict[str, Any]]) -> str:
    by_state: dict[str, list[str]] = defaultdict(list)
    for row in cities:
        by_state[row["state_code"]].append(row["city"])

    lines = [
        "# SWT Market City Index",
        "",
        "按州导航城市记录；详细字段与 participant count 以 `city_summary.json` 为准。",
        "",
    ]
    for state in sorted(states, key=lambda row: row["state"]):
        lines.extend((f"## {state['state']}", ""))
        for city in sorted(by_state.get(state["state_code"], []), key=str.casefold):
            lines.append(f"- {city}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    state_payload, cleaned_states = read_json_records(CLEANED_ROOT / "swt_state_clean.json")
    city_payload, cleaned_cities = read_json_records(CLEANED_ROOT / "swt_city_clean.json")
    states = project(cleaned_states, STATE_FIELDS)
    cities = project(cleaned_cities, CITY_FIELDS)

    with (CLEANED_ROOT / "community_support_groups_clean.csv").open(
        encoding="utf-8-sig", newline=""
    ) as handle:
        support_rows = list(csv.DictReader(handle))
    support_groups = project(support_rows, SUPPORT_GROUP_FIELDS)

    counts = {
        "state": len(states),
        "city": len(cities),
        "support_group": len(support_groups),
    }
    if counts != EXPECTED_COUNTS:
        raise ValueError(f"Unexpected cleaned record counts: {counts}; expected {EXPECTED_COUNTS}")

    if len({row["state_code"] for row in states}) != len(states):
        raise ValueError("State records contain duplicate state_code values")
    if len({(row["state_code"], row["city"]) for row in cities}) != len(cities):
        raise ValueError("City records contain duplicate (state_code, city) keys")

    state_totals = participant_totals(cleaned_states)
    city_totals = participant_totals(cleaned_cities)
    if state_totals != city_totals:
        raise ValueError(f"Cleaned state/city participant totals disagree: {state_totals} != {city_totals}")
    if participant_totals(states) != state_totals or participant_totals(cities) != city_totals:
        raise ValueError("Projected output participant totals differ from cleaned input")

    metadata = json.loads((CLEANED_ROOT / "source_metadata.json").read_text(encoding="utf-8"))
    # Keep source-only raw/current file inventories outside the installable Skill.
    metadata.pop("raw_files", None)
    metadata.pop("input_files", None)
    metadata.pop("cleaning_script", None)
    metadata["runtime_layer"] = {
        "name": "swt_market",
        "generated_from": "externally maintained cleaned aggregates",
    }

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    write_json(OUTPUT_ROOT / "state_summary.json", states)
    write_json(OUTPUT_ROOT / "city_summary.json", cities)
    write_json(OUTPUT_ROOT / "support_groups.json", support_groups)
    write_json(OUTPUT_ROOT / "source_metadata.json", metadata)
    (OUTPUT_ROOT / "README.md").write_text(README, encoding="utf-8")
    (OUTPUT_ROOT / "methodology.md").write_text(METHODOLOGY, encoding="utf-8")
    (OUTPUT_ROOT / "STATE_INDEX.md").write_text(build_state_index(states), encoding="utf-8")
    (OUTPUT_ROOT / "CITY_INDEX.md").write_text(
        build_city_index(states, cities), encoding="utf-8"
    )

    for label, filename, total in (
        ("state", "state_summary.json", state_totals),
        ("city", "city_summary.json", city_totals),
        ("support_group", "support_groups.json", None),
    ):
        print(f"{filename}: {counts[label]} records")
        if total is not None:
            print(
                "  participant totals: "
                + ", ".join(f"{key}={value}" for key, value in total.items())
            )
    print("Participant totals: unchanged from cleaned input; state and city aggregates agree.")
    print(f"Generated files: 8 under {OUTPUT_ROOT}")


if __name__ == "__main__":
    main()
