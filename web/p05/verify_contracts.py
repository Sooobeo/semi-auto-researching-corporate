"""Validate the subset of JSON Schema used by the P06/P07 generated contracts.

No additional dependency is required. Unsupported schema keywords fail closed.
"""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def validate(value,schema):
    supported={'$schema','type','required','properties','const','enum','minimum','minItems','allOf','if','then'}
    if set(schema)-supported:raise ValueError('Unsupported schema keyword')
    if 'const' in schema and value!=schema['const']:raise ValueError('const')
    if 'enum' in schema and value not in schema['enum']:raise ValueError('enum')
    types={'object':lambda x:isinstance(x,dict),'array':lambda x:isinstance(x,list),'string':lambda x:isinstance(x,str),'null':lambda x:x is None,'integer':lambda x:isinstance(x,int) and not isinstance(x,bool)}
    if 'type' in schema:
        ts=schema['type'] if isinstance(schema['type'],list) else [schema['type']]
        if not any(types[t](value) for t in ts):raise ValueError('type')
    if isinstance(value,dict):
        if not set(schema.get('required',[]))<=set(value):raise ValueError('required')
        for k,s in schema.get('properties',{}).items():
            if k in value:validate(value[k],s)
    if 'minimum' in schema and value<schema['minimum']:raise ValueError('minimum')
    if 'minItems' in schema and len(value)<schema['minItems']:raise ValueError('minItems')
    for sub in schema.get('allOf',[]):validate(value,sub)
    if 'if' in schema:
        try:validate(value,schema['if'])
        except ValueError:return
        validate(value,schema.get('then',{}))

if __name__=='__main__':
    phases=json.loads((Path(__file__).parent/'dist/phases.json').read_text('utf-8'))
    counts={}
    for phase,folder,schema_name,records_name in [('P06','p5','review_schema.json','ranking_predictions.jsonl'),('P07','p6','change_schema.json','change_records.jsonl')]:
        path=ROOT/'artifacts/us_equity'/folder/'runs'/phases['source_runs'][phase]
        schema=json.loads((path/schema_name).read_text('utf-8'));records=[json.loads(l) for l in (path/records_name).read_text('utf-8').splitlines()]
        for r in records:validate(r,schema)
        counts[phase]=len(records)
    try:validate({'status':'withheld','delta':'1','relative_delta':None}, {'allOf':[{'if':{'properties':{'status':{'const':'withheld'}}},'then':{'properties':{'delta':{'type':'null'}}}}]})
    except ValueError:negative=True
    else:negative=False
    if not negative:raise ValueError('Withheld schema negative case failed')
    print(json.dumps({'status':'passed','records':counts,'withheld_counterexample_rejected':negative,'validator':'documented JSON Schema subset; not a general-purpose validator'}))
