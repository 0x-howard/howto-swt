# 中美交通估算 · 数据蒸馏与算法

更新日期：2026-11-18e。约束 [travel-estimate.json](travel-estimate.json)。**不是实时报价**。

## 内置算法（当前）

```
规划中心价 = 走廊底价 × (提前系数 / T-30基准) × 旺季系数 × 直飞系数
区间 = 中心价 × (1 ± half_spread)；deal／stretch 再乘 deal_ratio／stretch_ratio
```

| 因子 | 含义 | 默认 |
|---|---|---|
| 走廊底价 | 该走廊在 **提前 30 天、可转机** 下的来回／单程中心点 | 国际见 `international_base_cny_round_trip`；国内见 `domestic_base_usd_one_way` 或距离回退 |
| 提前系数 | 订票日距出发天数的分段曲线 | T-30＝1.00；T-7＝1.45；T-60≈0.90 |
| 旺季系数 | 出发月 | 6–8 月 1.15；5／9 月 1.05；其余 0.95 |
| 直飞系数 | `--direct` | 国际约 1.22 |

国内无城市对时：`max(min, min(max, 25 + 0.10 × 英里))`（Haversine）。

这比「三张静态表」更精确之处：同一走廊会随 **提前多久订、哪个月走、要不要直飞** 变，而不是永远同一组数字。

## 为什么不接实时 API

| 方案 | 精度 | 问题 |
|---|---|---|
| Amadeus／Sabre／Skyscanner | 高（当日价） | 要密钥、配额、合规；Skill 离线包不适用 |
| 爬 OTA | 表面准 | 脆弱、违 ToS、不稳定 |
| **底价×提前×旺季（本版）** | 规划级中高 | 无密钥；对齐本人实付；明示非锁价 |
| 纯 DOT／航旅均价当 mid | 易偏临时票 | 已降为交叉校验 |

若以后要「更准到可下单」，应外挂可选 API，不替换本离线模型作默认。

## 底价校准（人票，不算宠物）

来源：西米 `0_26SWT全流程`（2026）。

| 段 | 实付 | 用途 |
|---|---|---|
| 广州→东京→纽约 | ¥5,000 | 华南→美东国际底价锚（T-30 可转机） |
| NYC↔MYR | ¥588／¥650 | 东岸→MYR 国内底价 ≈ $85 OW |
| 纽约→多伦多→上海 | ¥6,673 | 帮带路由，不校准底价 |

交叉：DOT MYR–NYC 均价 $144 ≈ 底价×临近提前；航旅纵横中美均价／直飞中位 ≈ stretch。

## CLI

```bash
python3 scripts/travel_estimate.py --from 广州 --gateway 纽约 --to "Myrtle Beach"
python3 scripts/travel_estimate.py --from 盐城 --gateway 纽约 --to "Myrtle Beach" --advance-days 14 --month 6
python3 scripts/travel_estimate.py --from 上海 --gateway 洛杉矶 --advance-days 60 --month 9 --direct
```

## 禁止

- 把帮带抵扣后净支出写成底价。  
- 把平台／DOT 均价塞回 T-30 底价。  
- 假装输出是锁仓价。
