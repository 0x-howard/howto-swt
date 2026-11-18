# 岗位 12 字段事实清单（仅内部）

读取 Offer 材料后，在**当前对话上下文**中维护与清洗 Skill 同构的 12 顶层字段清单。此清单只供同对话内清洗复用，**不得写入面向学生的回复、六维表或回本测算正文**。

## 何时写入

- 从 PDF、截图或文字提取岗位事实时，每识别出一个独立岗位，追加一条记录。
- 先按本 Skill 的 Offer 提取模板抄写计算输入；同时把同一批事实压成下面 12 字段，两套并存，互不替代。
- 材料未变时不重读原件重抽；用户更正某字段时只改对应记录。

## 字段契约（与清洗 `jobs.json` 顶层一致）

| 字段 | 格式 |
|---|---|
| `sponsor` | `string\|null` |
| `job` | `{"employer":string\|null,"title":string\|null}` |
| `state` | 美国两位州码或 `null` |
| `city` | 英文城市名或 `null` |
| `hourlyWage` | `{"min":number\|null,"max":number\|null}` |
| `weeklyHours` | `{"min":number\|null,"max":number\|null}` |
| `startDate` | `{"earliest":"YYYY-MM-DD"\|null,"latest":"YYYY-MM-DD"\|null}` |
| `endDate` | 同上 |
| `housingRentWeekly` | `number\|null`（USD/周） |
| `housingDeposit` | `number\|null` |
| `livingCostText` | `string\|null`（仅原文可证的生活设施／成本） |
| `notes` | `string\|null`（其余与该岗位相关的原文事实） |

未知填 `null`，不猜、不补零。基础时薪不含小费估算；押金与租金、管理费分开。

## 建议内部形状

```json
{
  "jobFacts": [
    {
      "sponsor": null,
      "job": {"employer": "Example Hotel", "title": "Housekeeping"},
      "state": "SC",
      "city": "Myrtle Beach",
      "hourlyWage": {"min": 16, "max": 16},
      "weeklyHours": {"min": 32, "max": 40},
      "startDate": {"earliest": "2027-05-15", "latest": "2027-06-01"},
      "endDate": {"earliest": "2027-09-01", "latest": "2027-09-30"},
      "housingRentWeekly": 125,
      "housingDeposit": 200,
      "livingCostText": "含WiFi、共用厨房",
      "notes": "需自备防滑鞋"
    }
  ],
  "sourceHints": [
    {"label": "用户上传的 Offer.pdf", "pagesOrRegion": "第1–2页"}
  ]
}
```

示例为结构说明，不代表真实岗位。有多个独立职位必须多条，不得合并成一条工资范围。

## 与分析输出的关系

- 六维分析、回本测算仍按本 Skill 规则，从 Offer 提取模板／`budget.py` 输入推导并展示。
- `jobFacts` 不替代六维，也不出现在学生可见结构里。
- 同对话用户要求清洗导出时，把已有 `jobFacts` 交给清洗 Skill；清洗不得再对同一材料做视觉／OCR 全量重认，除非用户提供了新文件或明确要求重读。
