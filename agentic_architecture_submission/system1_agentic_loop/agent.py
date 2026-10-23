"""A deterministic stop_reason-driven agent loop suitable for offline testing."""
from dataclasses import dataclass, asdict
from typing import Any

@dataclass
class Turn:
    index: int
    stop_reason: str
    tool_name: str | None = None
    tool_result: Any = None
    message: str = ""

class ModelAdapter:
    """Local scripted adapter. Replace with a provider-backed adapter as needed."""
    def __init__(self, scripted_turns): self.scripted_turns=list(scripted_turns); self.calls=0
    def next_turn(self, claim, tool_results):
        if self.calls >= len(self.scripted_turns):
            return {"stop_reason":"end_turn", "message":"No further action required."}
        turn=self.scripted_turns[self.calls]; self.calls+=1
        return dict(turn)

class AgentLoop:
    def __init__(self, model, tools, max_turns=12):
        self.model=model; self.tools=tools; self.max_turns=max_turns
    def run(self, claim):
        trace=[]; tool_results=[]; decision=None
        for i in range(self.max_turns):
            raw=self.model.next_turn(claim, tool_results)
            reason=raw.get('stop_reason')
            if reason not in {'tool_use','end_turn'}:
                raise ValueError(f"Unsupported stop_reason: {reason!r}")
            if reason=='tool_use':
                name=raw.get('tool_name')
                if name not in self.tools:
                    raise ValueError(f"Unknown tool: {name!r}")
                result=self.tools[name](claim, raw.get('arguments', {}))
                tool_results.append({"tool":name,"result":result})
                trace.append(asdict(Turn(i+1, reason, name, result, raw.get('message',''))))
                continue
            message=raw.get('message','')
            decision=route_claim(claim, message)
            trace.append(asdict(Turn(i+1, reason, None, None, message)))
            break
        else:
            decision={"status":"escalated","reason":"max_turns_exceeded"}
        return {"claim_id":claim.get('claim_id','unknown'),"decision":decision,"trace":trace}

def lookup_policy(claim, args):
    return {"policy_found": bool(claim.get('policy_id')), "policy_id":claim.get('policy_id')}
def check_completeness(claim, args):
    required=('claim_id','description','amount')
    missing=[k for k in required if k not in claim or claim[k] in (None,'')]
    return {"complete":not missing,"missing":missing}
def route_claim(claim, message):
    text=(message+' '+str(claim.get('description',''))).lower()
    if any(x in text for x in ('fraud','ambiguous','high risk','manual review')):
        return {"status":"escalated","reason":"risk_or_ambiguity"}
    if not claim.get('policy_id') or not claim.get('claim_id'):
        return {"status":"escalated","reason":"missing_required_information"}
    return {"status":"routed","queue":"standard_claims","reason":"eligible_for_standard_review"}

def demo_claims():
    return [
      {"claim_id":"CLM-1001","description":"Wind damage to roof","amount":1200,"policy_id":"POL-77"},
      {"claim_id":"CLM-1002","description":"Potential fraud: inconsistent receipts","amount":840,"policy_id":"POL-12"},
      {"claim_id":"CLM-1003","description":"Water damage","amount":500},
    ]
def run_demo():
    import json
    results=[]
    for claim in demo_claims():
        model=ModelAdapter([
          {"stop_reason":"tool_use","tool_name":"policy_lookup","arguments":{}},
          {"stop_reason":"tool_use","tool_name":"completeness_check","arguments":{}},
          {"stop_reason":"end_turn","message":"Review complete; route or escalate according to policy."},
        ])
        results.append(AgentLoop(model, {"policy_lookup":lookup_policy,"completeness_check":check_completeness}).run(claim))
    return results
if __name__=='__main__': print(json.dumps(run_demo(),indent=2))
