import json, os, urllib.request
from datetime import datetime, timezone
from pathlib import Path

STATE = Path('state.json')
URL = 'https://api.kraken.com/0/public/Ticker?pair=XRPEUR'

def main():
    with urllib.request.urlopen(URL, timeout=20) as response:
        data = json.load(response)
    if data.get('error'):
        raise RuntimeError(str(data['error']))
    ticker = next(iter(data['result'].values()))
    price = float(ticker['c'][0])
    state = json.loads(STATE.read_text()) if STATE.exists() else {'cash_eur':500.0,'xrp':0.0,'trades':[],'observations':[]}
    now = datetime.now(timezone.utc).isoformat()
    state['observations'].append({'time_utc':now,'xrp_eur':price})
    state['observations'] = state['observations'][-1000:]
    # Observation-only by default: no fabricated trading strategy or performance.
    state['last_update_utc'] = now
    state['equity_eur'] = round(state['cash_eur'] + state['xrp']*price, 2)
    STATE.write_text(json.dumps(state, indent=2) + '\n')
    print(f'XRP/EUR {price:.5f}; paper equity EUR {state["equity_eur"]:.2f}; observation recorded')

if __name__ == '__main__':
    main()
