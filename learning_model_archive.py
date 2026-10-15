"""Versioned, non-executable HYBRIXX model checkpoint archive.

Checkpoints are research snapshots only. Never restores weights into a trader.
A rollback selects a previously verified snapshot for analysis, not for orders.
"""
import hashlib
import json
import math
from datetime import datetime,timezone
from pathlib import Path
from learning_engine import FEATURE_NAMES
from learning_governance import COINS

MAX_VERSIONS=12

def checksum(payload):
    return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()

def verified(snapshot):
    try:
        payload=snapshot["payload"]
        if snapshot["sha256"]!=checksum(payload):return False
        if payload["trade_authorization"] is not False or set(payload["models"])!=set(COINS):return False
        for model in payload["models"].values():
            if model["feature_names"]!=list(FEATURE_NAMES):return False
            if model["holdout_model_frozen"] is not True:return False
            if model["signal_authorized"] is not False:return False
            if len(model["weights"])!=len(FEATURE_NAMES):return False
            if not all(isinstance(v,(float,int)) and not isinstance(v,bool) and math.isfinite(v) for v in model["weights"]+[model["bias"]]):return False
        return True
    except (KeyError,TypeError,ValueError):return False

def archive(report,existing=None):
    if report.get("trade_authorization") is not False or report.get("errors") or set(report.get("assets",{}))!=set(COINS):
        raise ValueError("INVALID_LEARNING_REPORT")
    models={}
    for coin,asset in report["assets"].items():
        models[coin]={"feature_names":asset["feature_names"],
                      "weights":asset["model_weights"],"bias":asset["model_bias"],
                      "holdout_model_frozen":asset["holdout_model_frozen"],
                      "signal_authorized":asset["signal_authorized"]}
    payload={"source_generated_utc":report["generated_utc"],
             "trade_authorization":False,"models":models}
    snapshot={"sha256":checksum(payload),"payload":payload}
    if not verified(snapshot):raise ValueError("INVALID_CHECKPOINT")
    old=existing if isinstance(existing,list) else []
    valid=[s for s in old if isinstance(s,dict) and verified(s)]
    if not any(s["sha256"]==snapshot["sha256"] for s in valid):
        valid.append(snapshot)
    return valid[-MAX_VERSIONS:]

def rollback_snapshot(history,sha256):
    """Read-only selection; no weights are installed or traded."""
    for snapshot in reversed(history):
        if isinstance(snapshot,dict) and snapshot.get("sha256")==sha256 and verified(snapshot):
            return snapshot
    raise ValueError("NO_VERIFIED_ROLLBACK")

def main():
    report=json.loads(Path("learning_engine_report.json").read_text(encoding="utf-8"))
    path=Path("learning_model_archive.json")
    previous=json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    snapshots=archive(report,previous)
    path.write_text(json.dumps(snapshots,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"snapshots":len(snapshots),"latest_sha256":snapshots[-1]["sha256"],
                      "restored_into_trading":False,"trade_authorization":False}))

if __name__=="__main__":main()
