#!/usr/bin/env python3
"""Validate structure and references only; never certify factual accuracy."""
import json
import sys
from datetime import date
from pathlib import Path

GROUPS = ('agencies', 'sponsors', 'relationships', 'locations', 'offers', 'cases',
          'documents', 'process_events')
STATUSES = {'verified', 'pending', 'conflicting', 'expired', 'historical'}
KINDS = {'official_rule', 'contract', 'written_reply', 'firsthand', 'marketing', 'assumption'}
FOREIGN = {'agency_id': 'agencies', 'sponsor_id': 'sponsors', 'location_id': 'locations',
           'offer_id': 'offers', 'document_id': 'documents'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def text(value):
    return isinstance(value, str) and bool(value.strip())


def valid_date(value, field):
    if value is not None:
        require(isinstance(value, str), field+': expected ISO date or null')
        parsed = date.fromisoformat(value)
        if field.endswith('checked_at'):
            require(parsed <= date.today(), field+': cannot be a future verification date')


def validate(data):
    require(isinstance(data, dict), 'input must be object')
    require(set(data) == {'schema_version', 'sources', *GROUPS}, 'unexpected or missing top-level fields')
    require(data['schema_version'] == '0.2', 'unsupported schema_version')
    for group in ('sources', *GROUPS):
        require(isinstance(data[group], list), group+': expected array')
    sources, all_ids, entity_ids = {}, set(), {}
    source_fields = {'id', 'kind', 'issuer', 'locator', 'location', 'published_at',
                     'checked_at', 'applicable_year', 'scope', 'permission', 'notes'}
    for src in data['sources']:
        require(isinstance(src, dict) and set(src) == source_fields, 'invalid source fields')
        for key in ('id', 'kind', 'issuer', 'locator', 'location', 'scope', 'permission'):
            require(text(src[key]), 'source.'+key+': nonempty string required')
        require(src['id'] not in all_ids, 'duplicate id: '+src['id'])
        all_ids.add(src['id'])
        require(src['kind'] in KINDS, 'invalid source kind')
        valid_date(src['published_at'], 'published_at')
        valid_date(src['checked_at'], 'checked_at')
        require(src['applicable_year'] is None or type(src['applicable_year']) is int, 'invalid source year')
        require(isinstance(src['notes'], str), 'source notes must be text')
        sources[src['id']] = src
    for group in GROUPS:
        entity_ids[group] = set()
        for entity in data[group]:
            require(isinstance(entity, dict) and set(entity) == {'id', 'label', 'claims'}, 'invalid entity fields')
            require(text(entity['id']) and text(entity['label']), 'entity id and label required')
            require(entity['id'] not in all_ids, 'duplicate id: '+entity['id'])
            all_ids.add(entity['id'])
            entity_ids[group].add(entity['id'])
    count, pending = 0, 0
    claim_fields = {'field', 'value', 'unit', 'applicable_year', 'status', 'source_ids', 'notes'}
    for group in GROUPS:
        for entity in data[group]:
            require(isinstance(entity['claims'], list), 'claims must be array')
            for claim in entity['claims']:
                count += 1
                require(isinstance(claim, dict) and set(claim) == claim_fields, 'invalid claim fields')
                require(text(claim['field']), 'claim field required')
                require(claim['unit'] is None or text(claim['unit']), 'unit must be text or null')
                require(claim['applicable_year'] is None or type(claim['applicable_year']) is int, 'invalid claim year')
                require(isinstance(claim['notes'], str), 'claim notes must be text')
                status = claim['status']
                require(status in STATUSES, 'invalid status')
                require(isinstance(claim['source_ids'], list), 'source_ids must be array')
                for sid in claim['source_ids']:
                    require(text(sid) and sid in sources, 'unknown source id')
                if status == 'pending':
                    pending += 1
                else:
                    require(bool(claim['source_ids']), 'non-pending claim requires source')
                if status == 'verified':
                    require(claim['value'] is not None, 'verified value cannot be null')
                    require(all(sources[s]['checked_at'] is not None for s in claim['source_ids']),
                            'verified claim requires dated verification for all sources')
                    require(all(sources[s]['kind'] not in {'assumption', 'marketing'} for s in claim['source_ids']),
                            'assumption or marketing cannot alone be labelled verified; retain as pending claim')
                if claim['field'] in FOREIGN and claim['value'] is not None:
                    require(text(claim['value']) and claim['value'] in entity_ids[FOREIGN[claim['field']]],
                            'foreign entity reference missing')
    return {'structure': 'passed', 'claims': count, 'pending_claims': pending,
            'readiness': 'empty template' if not count else 'requires factual and decision-specific review',
            'limit': '只验证结构与引用，不证明事实真实、适用当前年度或满足推荐条件'}


def main():
    if len(sys.argv) != 2:
        print('Usage: python3 scripts/validate_records.py INPUT.json', file=sys.stderr)
        return 2
    try:
        data = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'),
                          parse_constant=lambda value: (_ for _ in ()).throw(ValueError('invalid number: '+value)))
        print(json.dumps(validate(data), ensure_ascii=False, indent=2))
        return 0
    except (ValueError, TypeError, OSError, KeyError) as error:
        print('ERROR: '+str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
