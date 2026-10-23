import sys, json, sqlite3
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pytest
from orchestrator import *
def fixture(tmp_path):
 db=tmp_path/'d.sqlite'; init_db(db,[{'id':'1','shift':'day','severity':'high','status':'open','description':'x'},{'id':'2','shift':'night','severity':'low','status':'open','description':'y'},{'id':'3','shift':'day','severity':'low','status':'closed','description':'z'}]); return db
@pytest.mark.parametrize('shift,ids',[('day',['1']),('night',['2']),('missing',[])])
def test_sql_filter_shift(tmp_path,shift,ids): assert [x['id'] for x in query_shift(fixture(tmp_path),shift)]==ids
@pytest.mark.parametrize('i',range(6))
def test_hot_state_roundtrip(tmp_path,i):
 p=tmp_path/'hot.json'; s={'i':i}; write_hot_state(p,s); assert load_hot_state(p)==s
@pytest.mark.parametrize('size', [0,10,100,1000,3000])
def test_hot_state_under_budget(tmp_path,size):
 p=tmp_path/'hot.json'; n=write_hot_state(p,{'x':'a'*size}); assert n<HOT_BUDGET_BYTES
@pytest.mark.parametrize('age,mode',[(0,'resume'),(10,'resume'),(3599,'resume'),(3601,'fresh'),(9999,'fresh')])
def test_recovery_staleness(age,mode): assert recovery_decision({'timestamp':100},now=100+age,stale_seconds=3600)['mode']==mode
@pytest.mark.parametrize('checkpoint,mode',[ (None,'fresh'), ({'timestamp':100},'resume'), ({'timestamp':1},'fresh') ])
def test_recovery_missing_recent_stale(checkpoint,mode):
 now=100 if checkpoint and checkpoint['timestamp']==100 else 5000
 assert recovery_decision(checkpoint,now=now,stale_seconds=1000)['mode']==mode
@pytest.mark.parametrize('i',range(4))
def test_fork_isolated(i):
 main={'count':i,'nested':{'items':[]}}; fork=fork_investigation(main,'f','hypothesis'); fork['nested']['items'].append('x'); fork['fork']['scratchpad'].append('note'); assert main['nested']['items']==[] and 'fork' not in main
@pytest.mark.parametrize('i',range(5))
def test_hot_budget_rejects_large_state(tmp_path,i):
 with pytest.raises(ValueError): write_hot_state(tmp_path/'x.json',{'x':'z'*6000})
def test_run_shift_uses_filtered_slice(tmp_path):
 db=fixture(tmp_path); out=run_shift(db,tmp_path/'hot.json','day'); assert out['filtered_defect_count']==1 and out['defects'][0]['id']=='1'
def test_sql_parameters_not_interpolated(tmp_path):
 db=fixture(tmp_path); assert query_shift(db,"day' OR 1=1 --")==[]
