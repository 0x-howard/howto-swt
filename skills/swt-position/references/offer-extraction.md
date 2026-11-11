# Offer 字段提取模板

岗位 PDF、截图或文字先按本模板逐项抄写成 `scripts/budget.py` 的输入，再运行脚本，原样输出结果。只抄 Offer 上写明的事实；没写的字段直接省略，不猜测、不补零。

## 基础字段

| 字段 | Offer 常见标签 | 写法 |
|---|---|---|
| `label` | Job title / DBA | 雇主＋职位，如 `Dunkin Donuts 柜台员` |
| `city` / `state` | City / State | 原文城市名；州用两位缩写 |
| `wage_usd_per_hour` | Hourly wage (before taxes) | 数字，如 `14.5` |
| `hours_per_week` | Estimated hours per week / weekly average | 平均工时数字 |
| `min_hours` / `max_hours` | 工时区间 | 只有写明区间时填 |
| `hours_guaranteed` | guaranteed hours | 只有写明“保证”时填 `true` |
| `offer_start_date` / `offer_end_date` | Start / End date | `YYYY-MM-DD`；只写季节或“尽快”时省略 |
| `rent_usd_per_week` | Cost Amount + Cost Type | 换算成每周金额 |
| `food_usd_per_week` / `transport_usd_per_week` | 餐费、交通费 | 只有写明金额时填 |

## details 字段

| 字段 | Offer 常见标签 | 写法 |
|---|---|---|
| `sponsor` | 二工说明中的机构名 | 如 `CHI` |
| `tips` | Tips | `true` / `false` |
| `meals` | Meals / Meals details | 上班免费吃 `free_at_work`；员工折扣 `discount`；不提供 `none` |
| `meal_discount_percent` | 员工餐折扣 | 30% off 填 `30` |
| `housing_utilities_included` | Utilities included | `true` / `false` |
| `housing_deducted_from_pay` | Is housing cost deducted from paycheck | `true` / `false` |
| `housing_furnished_kitchen` | Additional housing features | 写明家具和厨房时填 `true` |
| `housing_deposit_usd` | Deposit amount | 数字；写明不收押金填 `0` |
| `housing_deposit_refundable` | Is housing deposit refundable | `true` / `false` |
| `housing_people_per_room` | Number of people to a room | 如 `2–4` |
| `housing_contract` | separate housing contract | `true` / `false` |
| `commute_walk_minutes` / `commute_bike_minutes` / `commute_drive_minutes` | Transportation details | 分钟数 |
| `employer_transport` | Method of transportation | 雇主接送 `provided`；协助安排 `assist`；自理 `none` |
| `second_job_allowed` | Possibility to find a second job | `true` / `false` |
| `ssn_required_before_work` | require SSN before arriving / starting | 要求先有 SSN 才能上班填 `true` |
| `ssn_employer_assist` | Social Security application assistance | `true` / `false` |
| `ssn_office` / `ssn_office_miles` | closest Social Security office / distance | 如 `Concord, NH` 与 `30` |
| `start` | When will work begin | 中文短语，如 `尽快` |
| `training_reduced_hours` | Conditions of training | 写明培训期工时偏少时填 `true` |
| `open_availability` | nights, weekends and holidays | 要求全时段可排班时填 `true` |
| `multiple_locations` | 门店数量 / work location may change | 门店数，如 `3` |
| `dress_code` | clothing / footwear | 一句中文：需自备的衣物 |
| `arrival` | Travel Instructions | 一句中文：机场到岗路线、接站、过夜 |
| `area` | Location details / Why choose us | 一句中文：地域特色 |
| `nearest_city` / `nearest_city_hours` | Location details（距某大城市几小时） | 如 `Boston` 与 `2` |
| `days_per_week` | Days per week / schedule | 每周上班天数，如 `5` |
| `amenities` | Nearby amenities / within walking distance | 步行可达的配套列表，如 `["超市", "洗衣房"]` |
| `customer_facing` | Job description（柜台、前台、服务员等面向顾客） | 面向顾客填 `true`；后厨、客房、仓库等后台填 `false` |
| `english_level` | English level required | 原文等级，如 `Intermediate` |
| `cultural_activities` | Cultural exchange activities | 一句中文：雇主组织的活动 |
| `roommates_international` | 住宿与其他国家学生合住 | 写明时填 `true` |

## 其他条款

以上字段都覆盖不到、但会影响选择的条款，写进 `cautions`，格式为 `{"短标题": "一句中文"}`。

## 示例

```json
{"mode":"position_overview","fx_cny_per_usd":6.8,"fx_source":"人民币中间价 6.7191","fx_quote_date":"2026-11-11","offers":[{"label":"Dunkin Donuts 柜台员","city":"Meredith","state":"NH","wage_usd_per_hour":14.5,"hours_per_week":32,"rent_usd_per_week":100,"details":{"sponsor":"CHI","tips":true,"meals":"free_at_work","housing_utilities_included":true,"housing_deducted_from_pay":true,"housing_furnished_kitchen":true,"housing_deposit_usd":0,"housing_people_per_room":"2–4","housing_contract":true,"commute_bike_minutes":40,"commute_drive_minutes":12,"employer_transport":"assist","second_job_allowed":true,"ssn_required_before_work":true,"ssn_employer_assist":true,"ssn_office":"Concord, NH","ssn_office_miles":30,"start":"尽快","training_reduced_hours":true,"open_availability":true,"multiple_locations":3,"dress_code":"自备防滑鞋、蓝色牛仔裤，以及纯黑或纯白的有领 Polo 衫。"}}]}
```
