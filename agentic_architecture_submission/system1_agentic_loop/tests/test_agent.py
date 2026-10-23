import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pytest
from agent import AgentLoop, ModelAdapter, lookup_policy, check_completeness, route_claim, demo_claims
TOOLS={"policy_lookup":lookup_policy,"completeness_check":check_completeness}
@pytest.mark.parametrize('i',range(10))
def test_valid_stop_reasons(i):
 m=ModelAdapter([{"stop_reason":"end_turn","message":"done"}]); r=AgentLoop(m,TOOLS).run({"claim_id":str(i),"policy_id":"p","description":"ok","amount":1}); assert r['trace'][-1]['stop_reason']=='end_turn'
@pytest.mark.parametrize('i',range(5))
def test_tool_use_continues(i):
 m=ModelAdapter([{"stop_reason":"tool_use","tool_name":"policy_lookup"},{"stop_reason":"end_turn","message":"done"}]); r=AgentLoop(m,TOOLS).run({"claim_id":"x","policy_id":"p","description":"ok","amount":1}); assert [t['stop_reason'] for t in r['trace']]==['tool_use','end_turn']
@pytest.mark.parametrize('desc,expected', [('potential fraud','escalated'),('ambiguous records','escalated'),('high risk case','escalated'),('routine roof repair','routed'),('standard water damage','routed')])
def test_routing(desc,expected): assert route_claim({"claim_id":"x","policy_id":"p","description":desc},'complete')['status']==expected
@pytest.mark.parametrize('claim,missing', [({},['claim_id','description','amount']),({'claim_id':'x'},['description','amount']),({'claim_id':'x','description':'d'},['amount']),({'claim_id':'x','description':'d','amount':1},[]),({'claim_id':'x','description':'','amount':1},['description'])])
def test_completeness(claim,missing): assert check_completeness(claim,{})['missing']==missing
@pytest.mark.parametrize('bad', ['pause','tool','',None,'completed'])
def test_bad_stop_reason_raises(bad):
 with pytest.raises(ValueError): AgentLoop(ModelAdapter([{"stop_reason":bad}]),TOOLS).run({})
