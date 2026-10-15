"""HYBRIXX Human Trader Research: public disclosures, never automatic copying.

The catalog is source-backed and deliberately contains NO invented returns or trade logs.
Use only public, authorized observations; profiles are not verified trading histories.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

SOURCES=[
 {"platform":"eToro","url":"https://www.etoro.com/de/copytrader/","data":"Public investor profiles, risk score, returns and portfolio information","limitations":"Displayed returns are not a complete verified trade-by-trade execution ledger."},
 {"platform":"eToro statistics","url":"https://help.etoro.com/s/article/What-statistics-does-eToro-track-and-where-can-I-find-them?language=en_GB","data":"Performance, diversification, risk, drawdown, trading statistics","limitations":"Metrics depend on profile visibility and platform methodology."},
 {"platform":"Bybit Master Trader","url":"https://www.bybit.com/en/help-center/article/How-to-Navigate-Copy-Trading-User-Center-Master-Trader","data":"90-day ROI, P&L, equity and order details where public","limitations":"Perpetual derivatives and leverage are not comparable to unleveraged spot trading."},
 {"platform":"CFTC risk guidance","url":"https://www.cftc.gov/LearnAndProtect/AdvisoriesAndArticles/AITradingBots.html","data":"Public warnings on unverifiable performance and AI trading claims","limitations":"Educational guidance, not trader performance data."}
]

def classify(record):
    """No positive classification without independently documented trade data."""
    reasons=[]
    for field in ("source_url","observed_utc","period_days","max_drawdown_pct","return_pct","trade_count","verified_execution_history"):
        if record.get(field) is None: reasons.append("MISSING_"+field.upper())
    if record.get("verified_execution_history") is not True:
        reasons.append("UNVERIFIED_EXECUTION_HISTORY")
    if record.get("period_days",0)<180: reasons.append("SHORT_TRACK_RECORD")
    if record.get("trade_count",0)<30: reasons.append("FEW_TRADES")
    if record.get("max_drawdown_pct",100)>15: reasons.append("HIGH_DRAWDOWN")
    if record.get("return_pct",-100)<=0: reasons.append("NONPOSITIVE_RETURN")
    return {"status":"RESEARCH_REVIEW" if not reasons else "UNVERIFIED_DO_NOT_COPY","reasons":reasons}

def report():
    return {"generated_utc":datetime.now(timezone.utc).isoformat(),
            "mode":"READ_ONLY_HUMAN_TRADER_RESEARCH",
            "source_catalog":SOURCES,
            "candidate_profiles":[],
            "screening_policy":{"minimum_history_days":180,"minimum_trade_count":30,
                                "max_drawdown_pct":15,"verified_execution_history_required":True},
            "integration":"Observe human decision patterns for research only; never submit or mirror orders.",
            "note":"No individual trader was verified; public profile rankings are not execution records."}

def main():
    output=Path("human_trader_research.json")
    output.write_text(json.dumps(report(),ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Saved read-only public trader research catalog.")
if __name__=="__main__":main()
