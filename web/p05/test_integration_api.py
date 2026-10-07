"""Exercise the actual loopback API without exposing its anti-CSRF token."""
import argparse
import http.client
import json
import sys
import time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'scripts'))
from p08_common import atomic,read,now

def check(port,report):
    def req(method,path,headers=None,body=None):
        c=http.client.HTTPConnection('127.0.0.1',port,timeout=15)
        c.request(method,path,body=body,headers=headers or {});r=c.getresponse();status=r.status;raw=r.read();c.close()
        try:d=json.loads(raw)
        except ValueError:d=None
        return status,d
    result={};status,session=req('GET','/api/p08-state');result['local_state']=status==200 and session['enabled']
    token=session['token'];headers={'X-P05-Token':token}
    _,prior=req('GET','/integration.json'); expected_p09_source=prior['P09']['source_p08_run']
    result['missing_token_rejected']=req('POST','/api/run-p08')[0]==403
    result['cross_origin_rejected']=req('POST','/api/run-p08',{**headers,'Origin':'https://example.invalid'})[0]==403
    result['untrusted_host_rejected']=req('GET','/api/p08-state',{'Host':'example.invalid'})[0]==403
    result['arbitrary_path_rejected']=req('GET','/private/not-a-file')[0]==404
    result['unknown_endpoint_rejected']=req('POST','/api/delete',headers)[0]==404
    result['large_request_rejected']=req('POST','/api/feedback',{**headers,'Content-Length':'512001'})[0]==413
    status,job=req('POST','/api/run-p08',headers);result['actual_pipeline_started']=status==202
    end=time.monotonic()+90
    while time.monotonic()<end:
        status,job=req('GET','/api/p08-job')
        if not job['busy']:break
        time.sleep(.2)
    result['actual_pipeline_completed']=job['stage']=='done' and not job['error']
    status,snapshot=req('GET','/integration.json')
    result['local_result_updated']=status==200 and snapshot['P08']['run_id']==job['run_id']
    result['candidate_denominator']=snapshot['P08']['summary']['candidates']==39 and len(snapshot['P08']['cards'])==33
    result['p09_frozen_source_preserved']=snapshot['P09'] is not None and snapshot['P09']['source_p08_run']==expected_p09_source
    data={'checked_at':now(),'checks':result,'status':'passed' if all(result.values()) else 'failed',
        'local_replay_run':job['run_id'],'external_calls':0,'human_participants':0,'credentials_in_report':False}
    atomic(report,data);return data

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8767);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
    r=check(a.port,a.report);print(json.dumps(r));raise SystemExit(r['status']=='failed')
