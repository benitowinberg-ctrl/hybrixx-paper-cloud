#!/usr/bin/env python3
"""Fetch public Kraken XRPEUR hourly CLOSED candles into Evolution Lab CSV.

Research data only; never touches account state, orders, or emergency locks.
"""
import csv
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

URL = "https://api.kraken.com/0/public/OHLC?pair=XRPEUR&interval=60"
DEST = Path(__file__).resolve().parent / "data" / "xrp_eur_1h.csv"

def main():
    req = urllib.request.Request(URL, headers={"User-Agent": "HYBRIXX-Evolution-Research/0.1"})
    with urllib.request.urlopen(req, timeout=25) as response:
        data = json.load(response)
    if data.get("error"):
        raise RuntimeError("Kraken API returned an error: " + repr(data["error"]))
    pairs = [key for key in data.get("result", {}) if key != "last"]
    if len(pairs) != 1:
        raise RuntimeError("Unexpected Kraken response pair count")
    raw = data["result"][pairs[0]]
    current_hour = int(datetime.now(timezone.utc).timestamp()) // 3600 * 3600
    candles = sorted(
        ((int(c[0]), float(c[4])) for c in raw if int(c[0]) < current_hour),
        key=lambda x: x[0],
    )
    if len(candles) < 240:
        raise RuntimeError("Not enough closed candles")
    if any(b[0] - a[0] != 3600 for a, b in zip(candles, candles[1:])):
        raise RuntimeError("Missing or irregular hourly candles; refusing incomplete CSV")
    if any(price <= 0 for _, price in candles):
        raise RuntimeError("Invalid non-positive close")
    DEST.parent.mkdir(parents=True, exist_ok=True)
    with DEST.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["timestamp", "close"])
        for ts, price in candles:
            writer.writerow([datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), format(price, ".10g")])
    print(f"Wrote {len(candles)} Kraken XRPEUR closed hourly candles to {DEST}")

if __name__ == "__main__":
    main()
