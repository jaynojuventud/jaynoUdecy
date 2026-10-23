import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pytest
from context import estimate_tokens, assemble_context, answer_question, evaluate, build_budget, demo
@pytest.mark.parametrize('s,n', [('',0),('a',1),('abcd',1),('abcde',2),('12345678',2),('x'*40,10),('x'*41,11),('hello',2),('  ',1),('unicode ✓',3)])
def test_token_estimator(s,n): assert estimate_tokens(s)==n
@pytest.mark.parametrize('key,val', [('claim_id','C1'),('amount',5),('policy_id','P1'),('description','damage'),('risk','low')])
def test_case_facts_preserved(key,val): assert str(val) in assemble_context({key:val},[],[])['case_facts']
@pytest.mark.parametrize('question,expected', [('amount',True),('policy',True),('claim id',True),('damage',True),('fraud',False)])
def test_answerability(question,expected):
 c=assemble_context({'claim_id':'C1','amount':4,'description':'damage'},[],['policy alpha']); assert answer_question(c,question)==expected
@pytest.mark.parametrize('limit', [0,1,10,20,50])
def test_history_bounded(limit):
 c=assemble_context({},['word '*100],[],max_history_chars=limit); assert len(c['history_summary']) < 250
@pytest.mark.parametrize('i',range(4))
def test_budget_shape(i):
 b=build_budget({'x':'a'*i},{'x':'a'}); assert b['raw_baseline_tokens']>=b['assembled_context_tokens']
def test_demo_has_ablation_regression():
 d=demo(); assert any(d['full_evaluation'][q] and not d['control_without_case_facts'][q] for q in d['questions'])
