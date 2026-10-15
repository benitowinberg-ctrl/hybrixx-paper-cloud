"""HYBRIXX Intelligence Core governance. Research only; never routes orders."""
import math
from datetime import datetime,timezone

REQUIRED_MODULES=("evolution","copy_trading","special_situations")

def evaluate(report):
    """Fail-closed research selection: negative/insufficient evidence => no champion."""
    if report.get("mode")!="RESEARCH_ONLY":
        raise ValueError("Only RESEARCH_ONLY reports are accepted")
    evolution=report.get("evolution",{})
    ranking=evolution.get("ranking",[])
    if not isinstance(ranking,list):
        raise ValueError("Invalid ranking")
    audited=[]
    for row in ranking:
        score=row.get("mean_oos_return_pct")
        dd=row.get("worst_oos_drawdown_pct")
        folds=row.get("folds")
        positive=row.get("positive_folds")
        if not all(isinstance(v,(int,float)) and math.isfinite(v) for v in (score,dd,folds,positive)):
            raise ValueError("Invalid performance metrics")
        if folds<3 or dd<0 or positive<0 or positive>folds:
            raise ValueError("Invalid fold statistics")
        # Deliberately conservative: short 30-day Kraken dataset cannot qualify for deployment.
        audited.append({"strategy":str(row["strategy"]),"research_score":round(score-.5*dd,4),
                        "status":"EXPLORATORY_ONLY"})
    return {"version":"0.2","generated_at_utc":datetime.now(timezone.utc).isoformat(),
            "operating_mode":"PAPER_RESEARCH_ONLY","trade_permission":False,
            "automatic_order_execution":False,"champion":None,
            "research_candidates":sorted(audited,key=lambda x:x["research_score"],reverse=True),
            "modules":{"evolution":"AUTOMATED_WALK_FORWARD",
                       "copy_trading":report.get("copy_trading",{}).get("status","NO_DATA"),
                       "special_situations":report.get("special_situations",{}).get("status","NO_DATA")},
            "restrictions":["No exchange credentials","No live or paper order generation",
                            "No override of emergency stop","No promotion from short-window backtests"],
            "explanation":"Automatic parameter evaluation is research, not autonomous model training or verified alpha."}
