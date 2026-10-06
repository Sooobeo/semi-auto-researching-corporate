"""Reference-free structural checks for selected observations."""
from p05_common import normalize_fragment

def check_input(r, schema_validator):
    errors=['schema:'+('/'.join(map(str,e.absolute_path)) or 'root') for e in schema_validator.iter_errors(r)]
    if errors: return sorted(set(errors))
    ev=r['evidence']; bykind={e['kind']:e for e in ev}; raw=r['raw']
    expected={'row_label','period_header','year_header','unit'}
    if r['input_kind']=='numeric_cell': expected.add('numeric_value')
    if set(bykind)!=expected or len(bykind)!=len(ev): errors.append('evidence_kind_cardinality')
    if len({e['table_id'] for e in ev})!=1: errors.append('cross_table_binding')
    for e in ev:
        o=e['fragment_origin']; a=e['start']-o; b=e['end']-o
        if not (0<=a<b<=len(e['raw_fragment'])) or e['raw_fragment'][a:b]!=e['selected_text']:
            errors.append('fragment_span_roundtrip')
        n,m=normalize_fragment(e['raw_fragment'],o)
        if n!=e['normalized_fragment'] or m!=e['normalized_to_raw']: errors.append('normalization_offset_map')
        if not e['location'].startswith(e['table_id']+'/'): errors.append('table_location_binding')
    for key,kind in [('row_label','row_label'),('period_header','period_header'),('year_header','year_header'),('unit_header','unit')]:
        if kind not in bykind or raw[key]!=bykind[kind]['selected_text']: errors.append(key+'_evidence_binding')
    if r['input_kind']=='numeric_cell' and 'numeric_value' in bykind:
        e=bykind['numeric_value']; label=bykind.get('row_label',{})
        if raw['value_cell']!=e['raw_fragment']: errors.append('numeric_cell_evidence_binding')
        if e['row_index']!=label.get('row_index') or e['location'].rsplit('/',1)[0]!=label.get('location','').rsplit('/',1)[0]:
            errors.append('row_binding')
        if set(e['header_refs'])!={x['evidence_id'] for x in ev if x['kind']!='numeric_value'}:
            errors.append('header_binding')
    return sorted(set(errors))
