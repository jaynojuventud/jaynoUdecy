"""Tiered state orchestration with SQL filtering, checkpoint recovery, and isolated forks."""
import json, sqlite3, time
from pathlib import Path

HOT_BUDGET_BYTES=5*1024
DEFAULT_STALE_SECONDS=3600

def init_db(path, defects):
    con=sqlite3.connect(path); con.execute('CREATE TABLE IF NOT EXISTS defects (id TEXT PRIMARY KEY, shift TEXT, severity TEXT, status TEXT, description TEXT)')
    con.execute('DELETE FROM defects'); con.executemany('INSERT INTO defects VALUES (?,?,?,?,?)',[(d['id'],d['shift'],d['severity'],d['status'],d['description']) for d in defects]); con.commit(); con.close()
def query_shift(path, shift):
    con=sqlite3.connect(path); con.row_factory=sqlite3.Row
    rows=[dict(r) for r in con.execute('SELECT id, shift, severity, status, description FROM defects WHERE shift = ? AND status != ? ORDER BY id',(shift,'closed'))]
    con.close(); return rows

def write_hot_state(path, state, budget=HOT_BUDGET_BYTES):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True); payload=json.dumps(state,sort_keys=True,separators=(',',':'))
    if len(payload.encode())>=budget: raise ValueError(f'hot state exceeds budget: {len(payload.encode())} >= {budget}')
    p.write_text(payload); return len(payload.encode())
def load_hot_state(path): return json.loads(Path(path).read_text())
def recovery_decision(checkpoint, now=None, stale_seconds=DEFAULT_STALE_SECONDS):
    now=time.time() if now is None else now
    if not checkpoint: return {'mode':'fresh','reason':'no_checkpoint'}
    age=max(0,now-float(checkpoint.get('timestamp',0)))
    if age>stale_seconds: return {'mode':'fresh','reason':'checkpoint_stale','age_seconds':age,'threshold_seconds':stale_seconds}
    return {'mode':'resume','reason':'checkpoint_recent','age_seconds':age,'threshold_seconds':stale_seconds}
def fork_investigation(main_state, fork_id, hypothesis):
    # JSON round-trip ensures a deep copy; scratchpad exists only in returned fork state.
    fork=json.loads(json.dumps(main_state)); fork['fork']={'id':fork_id,'hypothesis':hypothesis,'scratchpad':[]}; return fork
def run_shift(db_path, hot_path, shift='day'):
    defects=query_shift(db_path,shift)
    state={'shift':shift,'processed_defect_ids':[d['id'] for d in defects],'open_count':len(defects),'last_run':'shift-review-v1'}
    size=write_hot_state(hot_path,state)
    return {'shift':shift,'filtered_defect_count':len(defects),'defects':defects,'hot_state_bytes':size,'hot_state_budget_bytes':HOT_BUDGET_BYTES,'state':state}

def demo(base_dir):
    base=Path(base_dir); base.mkdir(parents=True,exist_ok=True); db=base/'defects.sqlite'; hot=base/'hot_state.json'
    defects=[{'id':'D-101','shift':'day','severity':'high','status':'open','description':'sensor drift'},{'id':'D-102','shift':'day','severity':'medium','status':'investigating','description':'seal wear'},{'id':'D-103','shift':'night','severity':'low','status':'open','description':'label mismatch'},{'id':'D-104','shift':'day','severity':'low','status':'closed','description':'resolved scratch'}]
    init_db(db,defects); run=run_shift(db,hot,'day'); checkpoint={'timestamp':10000,'state':load_hot_state(hot)}
    resume=recovery_decision(checkpoint,now=11000,stale_seconds=3600); stale=recovery_decision(checkpoint,now=15000,stale_seconds=3600)
    fork=fork_investigation(run['state'],'fork-A','sensor drift caused by calibration')
    fork['fork']['scratchpad'].append('inspect calibration log')
    return {'run':run,'recovery_recent':resume,'recovery_stale':stale,'main_state_after_fork':load_hot_state(hot),'fork_state':fork}
if __name__=='__main__':
 import sys; print(json.dumps(demo(sys.argv[1] if len(sys.argv)>1 else 'artifacts'),indent=2))
