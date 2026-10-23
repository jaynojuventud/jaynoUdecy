from pathlib import Path
import json, subprocess, sys
ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'artifacts'
(ART/'test_logs').mkdir(parents=True,exist_ok=True)
suites=[('system1_agentic_loop',30),('system2_context_strategy',30),('system3_claude_harness',35),('system4_orchestration',33)]
results=[]
for folder,count in suites:
    cmd=[sys.executable,'-m','pytest',str(ROOT/folder/'tests'),'-q']
    p=subprocess.run(cmd,cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    log=(f"SYSTEM: {folder}\nCOMMAND: {' '.join(cmd)}\nEXPECTED_TESTS: {count}\n"
         f"EXIT_CODE: {p.returncode}\n\n{p.stdout}")
    (ART/'test_logs'/f'{folder}.log').write_text(log)
    results.append({'system':folder,'expected_tests':count,'exit_code':p.returncode,'output':p.stdout})
sys.path.insert(0,str(ROOT/'system1_agentic_loop'))
from agent import run_demo
(ART/'agentic_run.json').write_text(json.dumps(run_demo(),indent=2))
sys.path.insert(0,str(ROOT/'system2_context_strategy'))
from context import demo as context_demo
ctx=context_demo()
(ART/'context_run.json').write_text(json.dumps(ctx,indent=2))
(ART/'budget.json').write_text(json.dumps(ctx['budget'],indent=2))
sys.path.insert(0,str(ROOT/'system3_claude_harness'))
from validate import validate
(ART/'harness_validation.json').write_text(json.dumps(validate(),indent=2))
sys.path.insert(0,str(ROOT/'system4_orchestration'))
from orchestrator import demo as orchestration_demo
orch=orchestration_demo(ART/'orchestration')
(ART/'orchestration_run.json').write_text(json.dumps(orch,indent=2))
summary={'total_expected_tests':sum(x[1] for x in suites),'all_passed':all(x['exit_code']==0 for x in results),
         'suites':[{'system':r['system'],'expected_tests':r['expected_tests'],'exit_code':r['exit_code']} for r in results]}
(ART/'test_summary.json').write_text(json.dumps(summary,indent=2))
for r in results:
    print(f"[{r['system']}] exit={r['exit_code']}\n{r['output']}")
print('SUMMARY:',json.dumps(summary))
if not summary['all_passed']: raise SystemExit(1)
