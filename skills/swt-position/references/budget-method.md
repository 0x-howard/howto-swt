# 预算方法与脚本接口

## SWT 岗位／Offer 概览（默认）

`scripts/budget.py` 的 `position_overview` 模式是岗位、Offer、城市＋岗位与回本问题的默认计算入口。最少每个岗位只需 `wage_usd_per_hour` 和 `hours_per_week`；其他普通缺口按 `references/default-assumptions.json` 的城市 → 州 → 通用值补齐。州级周租取 `state_context` 的范围中值；“每周基础开销”仅作餐饮规划代理，不冒充城市食品均价。所有回退字段在结构化结果中带来源，在用户表格中标“估”。

输入示例见 `assets/position-overview-example.json`。默认输出固定为一句结论、六维核心数据表、回本测算表、并列注意事项表和一个选择题；`--json` 可取得全部计算字段、默认值来源与税务前提。详细口径在用户追问时展开，不把完整 JSON 倾倒到首答。

- 工作期：用户日期 → Offer 日期 → 用户周数 → 集中默认周数。日期按含最后一个有薪工作日计算；另有停留周数时食宿按停留周数算。
- 税前工资＝时薪×每周工时×工作周数；预计税费优先本人明确输入，否则使用带税年的联邦税阶、已核验州税结论或州税规划预留，默认假设须标明。
- 在美净结余＝税前工资－预计税费－住宿－餐饮－交通－其他必要生活费；最终项目结余再减前期投入。人民币费用按本人汇率或集中维护的规划汇率转美元。
- 回本周数按本次估算的每周税后可结余金额推算，超过工作期需明确标出；它不是工时、费用或税务的保证。
- 未知小费、二工、退税、奖励与可退押金不进入默认收入。工资延迟到账也不自动等于工资损失；首薪现金需求可在后续 Detail View 单独展开。

运行：

```bash
python3 scripts/budget.py assets/position-overview-example.json
python3 scripts/budget.py --json assets/position-overview-example.json
python3 scripts/budget.py --detail housing assets/position-overview-example.json
```

## 旧版精细净收入接口（仍可按需使用）

提供 `tax_mode` 的旧输入仍走严格精细接口：它接受时薪、工时、日期或工作周数、房租、工作州、已知其他成本、税务模式和汇率，示例见 `assets/net-income-example.json`。以下“税费待核验时只显示未扣税金额”等规则仅适用于该接口，**不阻止默认概览使用明确标“估”的税务模型**。

- 日期的结束日按“预计最后一个有薪工作日”计入总天数；工作周数＝总天数／7。也可以直接输入工作周数。
- 同时给日期和周数且两者不一致时，脚本返回 `needs_confirmation`，不悄悄选择其中一个。
- 税前收入＝`时薪 × 每周工时 × 工作周数`，再加已明确的加班收入。
- 住宿＝`每周房租 × 工作周数`；其他已知成本＝每周交通、餐饮、其他周成本乘工作周数，加一次性成本。
- 税后预计净结余＝税前收入－预计税费－住宿－其他已知成本。税费待核验时只显示扣除已知成本后的金额，不伪造税后净额。
- `manual_rates` 仅使用用户明确输入的联邦与州税率；`data_assisted` 仅使用工资单扣缴和本地已核验州资料。两者都不把扣缴或退税当最终税负。
- 人民币结果只在给出用户指定或当轮核验的 `人民币／美元` 汇率后计算。

运行：

```bash
python3 scripts/budget.py assets/net-income-example.json
python3 scripts/budget.py --json assets/net-income-example.json
```

## 旧三情景现金流模型（非默认）

`scripts/compare_budget.py` 是保留的一工三情景现金流模型，不是税务计算器或推荐排序器。Python 3.10+，仅用标准库。输入示例在 `assets/budget-example.json`，全部为虚构数字。

## 输入

顶层字段：`evaluation_start`、`evaluation_end`（YYYY-MM-DD，末日不计入，统一比较期间）、`cny_per_usd`（每美元人民币，正数）、`available_cash_usd`（首薪前可用现金，换算口径自行说明）、`emergency_reserve_usd`、`assumptions`（非空说明数组）、`offers`（至少一项）。

每个 offer：`id`、`label`、`scenarios`。每项必须具备 `downside`、`base`、`upside` 三个情景。每个情景是下列非负数：

| 字段 | 口径 |
|---|---|
| work_weeks | 期间内有薪工作周数，不超过期间总周数 |
| regular_hours_per_week / regular_hourly_usd | 普通工时与每小时美元工资 |
| overtime_hours_per_week / overtime_hourly_usd | 已单列的额外工时与适用薪率；普通工时不能再包含这些工时；不自动假设 1.5 倍 |
| tips_total_usd | 全程小费；无证据时仅作为显式假设，保守情景设 0 并注明 |
| gross_pay_unreceived_usd | 截止比较末日尚未到账的税前工资及小费；与首薪和末薪日期有关 |
| withholding_total_usd | 期间已收工资对应的扣缴估计或实绩，来源须说明；不是最终应纳税额，不默认退税 |
| housing_weekly_usd | 按个人承担额统一折算到周的租金，含租赁周期说明 |
| food_weekly_usd / commute_weekly_usd / other_weekly_usd | 按整个停留期间计费，不能仅乘工作周数；额外旅行费等可计入一次性费用 |
| upfront_nonrefundable_usd | 一次性不退费用合计，包括已付成本；若只分析新增成本，另做同口径输入并明确标题 |
| refundable_deposit_paid_usd / deposit_returned_by_end_usd | 需支付的可退押金与期末前可到账返还；返还不能超过支付额；有疑问做不返还情景 |
| cash_living_before_first_pay_usd | 首薪前实际需支付的生活、交通及预付租金，属于总生活费的子集，只用于启动现金检查，不二次计入成本 |

JSON 不接受 null、字符串数字、NaN、Infinity 或布尔值冒充金额。未知值先补证或由用户确认明确假设，不能自动补零。字段名拼错或增加未支持字段时报错，防止静默漏算。

## 计算

- 停留周数＝两个日期之差／7，月租换算按实际合同计费期完成后再输入；脚本按周摊算，不自动处理整月起租、空置或提前退租罚金，需计入明确费用。
- 一工税前劳动收入＝工作周数×（普通周工时×普通薪率＋额外周工时×额外薪率）＋全程小费。
- 期内工资到账净额＝税前劳动收入－未到账税前收入－期内扣缴额。
- 生活费用＝停留周数×（房租＋食品＋交通＋其他周费用）。
- 期末净现金变化＝期内工资到账净额－生活费用－不退费用－支付押金＋期末前返还押金。
- 首薪前所需现金下限＝不退费用＋押金＋首薪前生活现金＋应急保留额。为简化起见，假设所有不退费用和押金在首薪前支付；这是保守准备口径，不是完整逐日现金流。
- 首薪前资金缺口＝max(0, 所需现金下限－可用现金)。

期末净现金变化不包括起始资金，也不是最终利润。未到账工资、未返还押金和未来税务结算单列，不能称为最终净收入。汇率仅统一换算，不预测未来波动。

脚本不计二工、银行奖励、推荐费、退税或投资收益。若需要比较这些事项，单独列增量情景及来源，不混入一工输出。本版不推算签证成功率、岗位稳定性或城市评分。

## 运行

在 skill 目录运行：

```bash
python3 scripts/compare_budget.py assets/budget-example.json
python3 scripts/validate_records.py assets/collection-records.json
python3 tests/test_plugin.py
```

输出到标准输出；需要保存时由调用方指定文件，脚本不修改输入。显示保留两位小数，内部使用 Decimal。结果顺序与输入一致，不以金额自动推荐。
