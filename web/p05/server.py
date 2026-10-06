"""Loopback-only companion: serve the same dashboard and execute the frozen P05 CLI."""
from __future__ import annotations
import argparse
import json
import os
import secrets
import subprocess
import sys
import threading
import uuid
from datetime import datetime,timezone
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
from snapshot import ROOT,DIST,snapshot

RUNS=ROOT/'artifacts/us_equity/p4_web_runs'
TOKEN=secrets.token_urlsafe(32)
LOCK=threading.Lock()
STATE={'busy':False,'stage':None,'run_id':None,'error':None,'run_dir':None}
STATIC={'/':'index.html','/index.html':'index.html','/app.js':'app.js','/styles.css':'styles.css','/favicon.svg':'favicon.svg','/snapshot.json':'snapshot.json'}

def worker():
    run_id='web_'+datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')+'_'+uuid.uuid4().hex[:8]
    output=RUNS/run_id
    with LOCK:STATE.update(run_id=run_id,error=None,stage='extract')
    env={**os.environ,'PYTHONIOENCODING':'utf-8'}
    stages=[('extract',['p05_rule_baseline.py','--run-id',run_id,'--output-dir',str(output)]),
            ('validate',['p05_validate_predictions.py','--run-dir',str(output)]),
            ('compare',['p05_compare_reference.py','--run-dir',str(output)])]
    try:
        for stage,args in stages:
            with LOCK:STATE['stage']=stage
            result=subprocess.run([sys.executable,str(ROOT/'scripts'/args[0]),*args[1:]],cwd=ROOT,
                                  env=env,capture_output=True,text=True,timeout=90)
            if result.returncode:
                raise RuntimeError(f'{stage} failed (exit {result.returncode})')
        snapshot(output)
        with LOCK:STATE.update(stage='done',run_dir=str(output))
    except Exception as exc:
        # Do not export subprocess logs, private source text, or environment values.
        with LOCK:STATE.update(stage='error',error=str(exc) if isinstance(exc,RuntimeError) else type(exc).__name__)
    finally:
        with LOCK:STATE['busy']=False

class Handler(BaseHTTPRequestHandler):
    def log_message(self,format,*args):pass
    def send(self,status,body,content_type='application/json; charset=utf-8'):
        if not isinstance(body,bytes):body=json.dumps(body,ensure_ascii=False).encode('utf-8')
        self.send_response(status);self.send_header('Content-Type',content_type)
        self.send_header('Content-Length',str(len(body)));self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(body)
    def do_GET(self):
        path=urlsplit(self.path).path
        if path=='/api/state':
            try:
                with LOCK:run_dir=STATE['run_dir'];job=dict(STATE)
                data=snapshot(Path(run_dir) if run_dir else None)
                data['local']=dict(enabled=True,token=TOKEN,job={k:v for k,v in job.items() if k!='run_dir'})
                self.send(200,data)
            except Exception:self.send(503,{'error':'실행 결과를 읽지 못했습니다. P05 검증 파일을 확인해 주세요.'})
        elif path=='/api/job':
            with LOCK:self.send(200,{k:v for k,v in STATE.items() if k!='run_dir'})
        elif path in STATIC:
            file=DIST/STATIC[path]
            if not file.exists():self.send(404,{'error':'파일 없음'});return
            types={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8',
                   '.css':'text/css; charset=utf-8','.svg':'image/svg+xml','.json':'application/json; charset=utf-8'}
            self.send(200,file.read_bytes(),types[file.suffix])
        else:self.send(404,{'error':'찾을 수 없는 경로'})
    def do_POST(self):
        if urlsplit(self.path).path!='/api/run':self.send(404,{'error':'찾을 수 없는 경로'});return
        origin=self.headers.get('Origin')
        if origin and origin not in (f'http://127.0.0.1:{self.server.server_port}',f'http://localhost:{self.server.server_port}'):
            self.send(403,{'error':'허용되지 않은 요청'});return
        if self.headers.get('X-P05-Token')!=TOKEN:self.send(403,{'error':'화면을 새로 열어 주세요.'});return
        with LOCK:
            if STATE['busy']:self.send(409,{'error':'이미 실행 중입니다.'});return
            STATE.update(busy=True,stage='starting',error=None)
        threading.Thread(target=worker,daemon=True).start()
        self.send(202,{'status':'started'})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8765);a=p.parse_args()
    server=ThreadingHTTPServer(('127.0.0.1',a.port),Handler)
    print(f'P05 dashboard ready: http://127.0.0.1:{server.server_port}',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:server.server_close()
