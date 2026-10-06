#!/usr/bin/env python3
"""First-job scenario arithmetic, not tax advice or recommendation ranking."""
import json
import sys
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

FIELDS = {
    'work_weeks', 'regular_hours_per_week', 'regular_hourly_usd',
    'overtime_hours_per_week', 'overtime_hourly_usd', 'tips_total_usd',
    'gross_pay_unreceived_usd', 'withholding_total_usd', 'housing_weekly_usd',
    'food_weekly_usd', 'commute_weekly_usd', 'other_weekly_usd',
    'upfront_nonrefundable_usd', 'refundable_deposit_paid_usd',
    'deposit_returned_by_end_usd', 'cash_living_before_first_pay_usd',
}
SCENARIOS = {'downside', 'base', 'upside'}


def exact_keys(obj, expected, path):
    if not isinstance(obj, dict):
        raise ValueError(f'{path}: expected object')
    if set(obj) != expected:
        raise ValueError(f'{path}: missing={sorted(expected-set(obj))}, unexpected={sorted(set(obj)-expected)}')


def number(value, path):
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        raise ValueError(f'{path}: requires an explicit finite nonnegative number')
    result = Decimal(str(value))
    if not result.is_finite() or result < 0:
        raise ValueError(f'{path}: requires an explicit finite nonnegative number')
    return result


def money(value):
    return str(value.quantize(Decimal('.01'), rounding=ROUND_HALF_UP))


def calculate(data):
    exact_keys(data, {'evaluation_start', 'evaluation_end', 'cny_per_usd',
                     'available_cash_usd', 'emergency_reserve_usd', 'assumptions', 'offers'}, 'input')
    start = date.fromisoformat(data['evaluation_start'])
    end = date.fromisoformat(data['evaluation_end'])
    if end <= start:
        raise ValueError('evaluation_end must be after evaluation_start')
    stay = Decimal((end-start).days) / Decimal(7)
    fx = number(data['cny_per_usd'], 'cny_per_usd')
    if fx == 0:
        raise ValueError('cny_per_usd must be positive')
    available = number(data['available_cash_usd'], 'available_cash_usd')
    reserve = number(data['emergency_reserve_usd'], 'emergency_reserve_usd')
    if not isinstance(data['assumptions'], list) or not data['assumptions'] or any(
        not isinstance(x, str) or not x.strip() for x in data['assumptions']
    ):
        raise ValueError('assumptions must contain nonempty descriptions of sources and assumptions')
    if not isinstance(data['offers'], list) or not data['offers']:
        raise ValueError('offers must contain at least one candidate')
    results, ids = [], set()
    for offer in data['offers']:
        exact_keys(offer, {'id', 'label', 'scenarios'}, 'offer')
        for field in ('id', 'label'):
            if not isinstance(offer[field], str) or not offer[field].strip():
                raise ValueError(f'offer.{field}: requires nonempty string')
        if offer['id'] in ids:
            raise ValueError('duplicate offer id')
        ids.add(offer['id'])
        exact_keys(offer['scenarios'], SCENARIOS, offer['id']+'.scenarios')
        output = {'id': offer['id'], 'label': offer['label'], 'scenarios': {}}
        for scenario in ('downside', 'base', 'upside'):
            raw = offer['scenarios'][scenario]
            path = offer['id']+'.'+scenario
            exact_keys(raw, FIELDS, path)
            n = {k: number(v, path+'.'+k) for k, v in raw.items()}
            if n['work_weeks'] > stay:
                raise ValueError(path+': work weeks exceed evaluation period')
            if n['regular_hours_per_week'] + n['overtime_hours_per_week'] > 168:
                raise ValueError(path+': combined weekly hours exceed 168')
            if n['overtime_hours_per_week'] and not n['overtime_hourly_usd']:
                raise ValueError(path+': extra hours require an explicit nonzero rate')
            if n['regular_hours_per_week'] and not n['regular_hourly_usd']:
                raise ValueError(path+': regular hours require a nonzero wage')
            gross = n['work_weeks'] * (
                n['regular_hours_per_week'] * n['regular_hourly_usd'] +
                n['overtime_hours_per_week'] * n['overtime_hourly_usd']) + n['tips_total_usd']
            received = gross - n['gross_pay_unreceived_usd'] - n['withholding_total_usd']
            if received < 0:
                raise ValueError(path+': unpaid pay plus withholding exceeds gross earnings')
            if n['deposit_returned_by_end_usd'] > n['refundable_deposit_paid_usd']:
                raise ValueError(path+': returned deposit exceeds paid deposit')
            living = stay * sum(n[k] for k in (
                'housing_weekly_usd', 'food_weekly_usd', 'commute_weekly_usd', 'other_weekly_usd'))
            if n['cash_living_before_first_pay_usd'] > living:
                raise ValueError(path+': first-pay living cash must be a subset of total living cost')
            expense = living + n['upfront_nonrefundable_usd']
            outstanding = n['refundable_deposit_paid_usd'] - n['deposit_returned_by_end_usd']
            cash_net = received - expense - outstanding
            startup = (n['upfront_nonrefundable_usd'] + n['refundable_deposit_paid_usd'] +
                       n['cash_living_before_first_pay_usd'] + reserve)
            output['scenarios'][scenario] = {
                'gross_earned_usd': money(gross),
                'pay_received_after_withholding_usd': money(received),
                'living_expenses_usd': money(living),
                'nonrefundable_total_cost_usd': money(expense),
                'gross_pay_not_yet_received_usd': money(n['gross_pay_unreceived_usd']),
                'deposit_not_returned_by_end_usd': money(outstanding),
                'net_cash_change_usd': money(cash_net),
                'net_cash_change_cny': money(cash_net*fx),
                'startup_cash_required_usd': money(startup),
                'startup_cash_gap_usd': money(max(Decimal(0), startup-available)),
            }
        results.append(output)
    return {
        'scope': '一工情景计算；不含二工、未来退税、奖励；不自动排名；不是最终利润或完整逐日现金流',
        'evaluation_start': start.isoformat(), 'evaluation_end_exclusive': end.isoformat(),
        'stay_weeks': str(stay), 'cny_per_usd': str(fx),
        'assumptions': data['assumptions'], 'offers': results,
    }


def main():
    if len(sys.argv) != 2:
        print('Usage: python3 scripts/compare_budget.py INPUT.json', file=sys.stderr)
        return 2
    try:
        data = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'), parse_float=Decimal)
        print(json.dumps(calculate(data), ensure_ascii=False, indent=2))
        return 0
    except (ValueError, TypeError, OSError, KeyError) as error:
        print('ERROR: '+str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
