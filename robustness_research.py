"""Read-only robustness diagnostics for rolling out-of-sample strategy results.

Never modifies the trade gate, paper ledger or broker. No external packages.
"""
import json
import math
import random
import statistics
from datetime import datetime,timezone
from pathlib import Path

def diagnostics(asset,seed=1701,replicates=2000):
    folds=asset["folds"]
    returns=[float(f["out_of_sample"]["return_pct"]) for f in folds]
    if len(returns)<3 or any(not math.isfinite(r) or r<=-100 for r in returns):
        raise ValueError("INSUFFICIENT_OR_INVALID_FOLDS")
    rng=random.Random(seed)
    samples=[]
    worst=[]
    for _ in range(replicates):
        draw=[rng.choice(returns) for _ in returns]
        samples.append(sum(draw)/len(draw))
        worst.append(min(draw))
    samples.sort()
    negative=sum(r<=0 for r in returns)
    return {
      "folds":len(returns),
      "mean_fold_return_pct":round(statistics.mean(returns),4),
      "median_fold_return_pct":round(statistics.median(returns),4),
      "worst_fold_return_pct":round(min(returns),4),
      "best_fold_return_pct":round(max(returns),4),
      "nonpositive_folds":negative,
      "bootstrap_mean_ci95_pct":[round(samples[int(.025*replicates)],4),round(samples[int(.975*replicates)-1],4)],
      "bootstrap_probability_mean_positive":round(sum(v>0 for v in samples)/replicates,4),
      "bootstrap_method":"Resample independent walk-forward fold returns; exploratory only",
      "eligible_for_live_or_paper_authorization":False,
      "caveat":"Three overlapping-regime folds are too few for reliable inference; bootstrap cannot fix inadequate history."
    }

def main():
    src=json.loads(Path("walkforward_report.json").read_text(encoding="utf-8"))
    result={"generated_utc":datetime.now(timezone.utc).isoformat(),
            "mode":"RESEARCH_ONLY_NO_ORDERS",
            "source_generated_utc":src["generated_utc"],
            "assets":{},"errors":{},
            "warning":"Exploratory bootstrap, NOT a trade signal. No new purchase authorization."}
    for coin,asset in src.get("assets",{}).items():
        try:result["assets"][coin]=diagnostics(asset)
        except (KeyError,TypeError,ValueError,ZeroDivisionError) as exc:
            result["errors"][coin]=type(exc).__name__
    Path("robustness_report.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"analyzed":len(result["assets"]),"errors":result["errors"]}))
    if not result["assets"]:raise SystemExit(1)
if __name__=="__main__":main()
