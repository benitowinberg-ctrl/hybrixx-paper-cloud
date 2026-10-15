"""Permission-first offline task planner for HYBRIXX Universal AI.

No model, shell, network, trading or credential access. Explicit approval required
for mutating tools; no tool execution occurs in this module.
"""
from dataclasses import dataclass,asdict
import json

READ_ONLY=frozenset({"memory.search","research.report.read"})
APPROVAL_REQUIRED=frozenset({"memory.remember","memory.forget","code.propose"})
KNOWN=READ_ONLY|APPROVAL_REQUIRED

@dataclass(frozen=True)
class Step:
    tool:str
    argument:str
    approved:bool=False

def evaluate(steps):
    decisions=[]
    for step in steps:
        if not isinstance(step,Step):
            raise TypeError("INVALID_STEP")
        known=step.tool in KNOWN
        allowed=known and (step.tool in READ_ONLY or step.approved is True)
        decisions.append({"tool":step.tool,"argument":step.argument,
                          "allowed":allowed,"reason":("UNKNOWN_TOOL" if not known else
                          "APPROVAL_REQUIRED" if not allowed else "PERMITTED")})
    return {"mode":"PLAN_ONLY_NO_EXECUTION","steps":decisions,
            "executed_tools":0,"trading_access":False}

def report_summary(path="unified_intelligence_report.json"):
    from pathlib import Path
    report=json.loads(Path(path).read_text(encoding="utf-8"))
    return {"status":report.get("research_status","UNKNOWN"),
            "veto_reasons":report.get("veto_reasons",[]),
            "trade_authorization":False}
