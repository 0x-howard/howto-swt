# 中美交通费用简单估算

只覆盖 **中国 ↔ 美国**。算法：**走廊底价 × 提前订票曲线 × 旺季系数**（可选直飞加价）。详见 [数据蒸馏与算法](travel-estimate-sources.md)。

## 何时用

学生问机票／来回大概多少时，在 `swt-arrival` 跑本脚本；宠物帮带转 `swt-yangmao`。

## 怎么跑

```bash
python3 scripts/travel_estimate.py --from 广州 --gateway 纽约 --to "Myrtle Beach"
python3 scripts/travel_estimate.py --from 盐城 --gateway 纽约 --to "Myrtle Beach" --advance-days 30 --month 6
python3 scripts/travel_estimate.py --from 上海 --gateway 纽约 --to "Myrtle Beach" --advance-days 10 --direct
```

| 参数 | 作用 |
|---|---|
| `--advance-days` | 提前订票天数，默认 30 |
| `--month` | 出发月 1–12（旺季系数） |
| `--direct` | 偏直飞 |
| `--one-way` | 单程 |
| `--json` | 机器可读 |

## 怎么说

1. 先报 **规划档**（默认提前约一个月、可转机），再报下沿／上沿。  
2. 已知出发月或很晚才订时，加上对应参数再跑，不要口头瞎乘。  
3. 国际段可提帮带一句；国内段说明几乎带不了宠物。  
4. 标「估」；购票前核验。
