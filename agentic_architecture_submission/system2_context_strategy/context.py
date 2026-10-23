"""Small context assembler with explicit preservation and ablation support."""
import json
from pathlib import Path

def estimate_tokens(text):
    # Stable estimate for comparison only; use a real model tokenizer in production.
    return max(1,(len(text)+3)//4) if text else 0

def assemble_context(case_facts, history, policies, max_history_chars=180):
    facts=json.dumps(case_facts,sort_keys=True,separators=(',',':'))
    policy_summary='; '.join(str(x) for x in policies)
    history_text=' '.join(str(x) for x in history)
    if len(history_text)>max_history_chars: history_text=history_text[:max_history_chars].rsplit(' ',1)[0]+' [history summarized]'
    return {"case_facts":facts,"policy_summary":policy_summary,"history_summary":history_text}

def answer_question(context, question):
    q=question.lower(); facts=context.get('case_facts','').lower(); policy=context.get('policy_summary','').lower(); history=context.get('history_summary','').lower()
    if 'amount' in q: return 'amount' in facts and any(c.isdigit() for c in facts)
    if 'policy' in q: return bool(policy)
    if 'claim id' in q or 'claim_id' in q: return 'claim_id' in facts
    if 'damage' in q: return 'damage' in facts or 'damage' in history
    if 'fraud' in q: return 'fraud' in facts or 'fraud' in history or 'fraud' in policy
    if 'history' in q: return bool(history)
    return bool(facts or policy or history)

def evaluate(context, questions): return {q:answer_question(context,q) for q in questions}
def build_budget(raw, context):
    raw_text=json.dumps(raw,sort_keys=True); assembled=json.dumps(context,sort_keys=True)
    rb=estimate_tokens(raw_text); ab=estimate_tokens(assembled)
    return {"raw_baseline_tokens":rb,"assembled_context_tokens":ab,"reduction_percent":round((1-ab/rb)*100,2) if rb else 0,"method":"ceil(chars/4), heuristic not model tokenizer"}

def demo():
    raw={"case_facts":{"claim_id":"C-204","amount":1200,"description":"wind damage","policy_id":"P-88","risk":"routine"},"history":["Claim opened Monday; intake agent recorded initial loss notice and confirmed contact details","Customer called twice to ask about expected inspection timing and claim status","Adjuster reviewed photos and documented roof damage visible near the western edge","Weather report attached with regional wind speeds and precipitation observations","Old unrelated claim from 2019 concerned a different vehicle and a separate policy","Automated notification delivered and customer acknowledged receipt","Call center note says the customer prefers afternoon callbacks","Legacy system synchronization completed without a data validation error","A duplicate attachment was detected and retained for audit history","Claims operations added a generic reminder to follow standard procedures"],"policies":["Claims over threshold require review","Suspected fraud escalates"]}
    ctx=assemble_context(raw['case_facts'],raw['history'],raw['policies'],max_history_chars=120)
    questions=['What is the amount?','What policy applies?','What is the claim ID?','Is there damage?','Does fraud matter?','Is history available?']
    full=evaluate(ctx,questions); ablated=evaluate({**ctx,"case_facts":""},questions)
    return {"raw":raw,"context":ctx,"budget":build_budget(raw,ctx),"questions":questions,"full_evaluation":full,"control_without_case_facts":ablated}
if __name__=='__main__': print(json.dumps(demo(),indent=2))
