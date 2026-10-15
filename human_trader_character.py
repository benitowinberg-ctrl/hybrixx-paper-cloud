"""Publicly documented human trader study; never mirrors positions or orders."""
import json
from datetime import datetime,timezone
from pathlib import Path
PROFILES=[
 {"name":"Tony Mai","source":"https://thefreedominvestor.com/track-record","platform":"eToro/BullAware","reported_annualized_pct":47.77,"as_of":"2026-07-31","record_type":"self-published summary linked to third-party tracking","verification":"REQUIRES_INDEPENDENT_VALIDATION","style":"long-term equity investment"},
 {"name":"thomaspj","source":"https://bullaware.com/factsheet/thomaspj","platform":"eToro/BullAware","reported_annualized_pct":27.32,"as_of":"2026-08-31","reported_one_year_pct":-17.15,"record_type":"public third-party factsheet","verification":"PROFILE_SUMMARY_ONLY","style":"equity macro trend; no leverage, no crypto"},
 {"name":"DVWR / KhaledELderginy","source":"https://www.darwinex.com/invest/DVWR","platform":"Darwinex","reported_annualized_pct":19.64,"as_of":"2026-10-15","reported_trade_count":839,"record_type":"public platform strategy statistics, before fees","verification":"PLATFORM_SUMMARY_ONLY","style":"managed-risk strategy, not directly comparable to spot crypto"}
]
PRINCIPLES=[
 {"principle":"Risk-adjusted evaluation","implementation":"Evaluate drawdown, consistency and exposure alongside returns","status":"RESEARCH"},
 {"principle":"Trend confirmation","implementation":"Study macro and technical trend filters without copying any individual","status":"RESEARCH"},
 {"principle":"Loss awareness","implementation":"Reject candidates with missing loss history and unverified execution logs","status":"RESEARCH"},
 {"principle":"Out-of-sample discipline","implementation":"Never tune strategies using their final evaluation window","status":"RESEARCH"},
 {"principle":"No trade is a valid decision","implementation":"Retain cash when independent tests fail conservative acceptance criteria","status":"RESEARCH"}
]
def report():
 return {"generated_utc":datetime.now(timezone.utc).isoformat(),"mode":"PUBLIC_HUMAN_TRADER_RESEARCH_ONLY",
         "profiles":PROFILES,"behavioral_principles":PRINCIPLES,
         "trading_permissions":"NONE","auto_copy_enabled":False,
         "limitations":"Annualized performance figures differ in period, fees and risk. Profiles are research examples, not a global ranking or verified individual order logs."}
def main():
 Path("human_trader_character.json").write_text(json.dumps(report(),ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print("Saved public trader research character; no orders or paper account modifications.")
if __name__=="__main__":main()
