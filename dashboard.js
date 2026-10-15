const $=id=>document.getElementById(id),money=n=>Number.isFinite(Number(n))?Number(n).toLocaleString('de-DE',{style:'currency',currency:'EUR'}):'—';
let state=null;
function pick(obj,keys){for(const k of keys){if(obj&&obj[k]!==undefined&&obj[k]!==null)return obj[k]}return null}
function draw(items){const svg=$('chart');if(items.length<2){svg.innerHTML='<line class="axis" x1="10" y1="210" x2="690" y2="210"/><text x="350" y="115" text-anchor="middle" fill="#aeb7cf" font-size="17">Für eine Kurve fehlen noch Messpunkte</text>';return}
const a=items.map(Number).filter(Number.isFinite),lo=Math.min(...a),hi=Math.max(...a),range=hi-lo||1;
const pts=a.map((v,i)=>`${20+i*660/(a.length-1)},${215-(v-lo)/range*185}`).join(' ');
svg.innerHTML=`<line class="axis" x1="10" y1="210" x2="690" y2="210"/><polyline class="line" points="${pts}"/>`;}
function render(s){state=s;const observations=s.history&& !Array.isArray(s.history) ? (s.history[$('coin').value]||[]).map((v,i)=>({symbol:$('coin').value+'/EUR',price_eur:v})) : (pick(s,['observations','history','quotes','price_history'])||[]);
const arr=Array.isArray(observations)?observations:[],coin=$('coin').value;
const relevant=arr.filter(x=>!x.symbol||String(x.symbol).toUpperCase().includes(coin));
const prices=relevant.map(x=>typeof x==='number'?x:pick(x,['price_eur','price','xrp_eur','rate'])).filter(x=>x!==null&&Number.isFinite(Number(x)));
const latest=arr.at(-1)||{};
const equity=pick(s,['paper_equity_eur','equity_eur','paper_equity','equity','balance_eur','balance','cash_eur']);
$('equity').textContent=money(equity);
$('invested').textContent=money((s.positions&&s.latest_prices_eur ? Object.entries(s.positions).reduce((sum,[coin,qty])=>sum+qty*(s.latest_prices_eur[coin]||0),0) : pick(s,['invested_eur','invested','open_positions_value_eur'])));
$('vault').textContent=money(pick(s,['profit_vault_eur','vault_eur','vault']));
const lastPrice=s.latest_prices_eur&&s.latest_prices_eur[coin]!=null?s.latest_prices_eur[coin]:coin==='XRP'?pick(s,['xrp_eur','xrp_price_eur','price_eur','last_price_eur','price'])??prices.at(-1)??pick(latest,['price_eur','price','xrp_eur']):prices.at(-1);
$('price').textContent=lastPrice===null||lastPrice===undefined?'—':Number(lastPrice).toLocaleString('de-DE',{maximumFractionDigits:6})+' €';
$('points').textContent=prices.length+' Messpunkte für '+coin;
draw(prices);
const when=pick(s,['last_update_utc','last_updated','updated_at','timestamp','last_observation','time'])??pick(latest,['time_utc','timestamp','time','date']);
$('updated').textContent=when&&!Number.isNaN(Date.parse(when))?new Date(when).toLocaleString('de-DE',{dateStyle:'medium',timeStyle:'short'}):'Zeitstempel nicht vorhanden';
const emergencyLock=s.emergency_lock&&s.emergency_lock.active===true;
$('emergency-panel').classList.toggle('locked',emergencyLock);
$('emergency-panel').querySelector('strong').textContent=emergencyLock?'🛑 NOTFALLSTOPP AKTIV – ALLE PAPER-TRADES GESPERRT':'🚨 HYBRIXX Notfallmodus';
$('status').textContent=emergencyLock?'🛑 NOTFALLSTOPP AKTIV':'● Daten geladen · Paper-Test';
const engine=s.paper_engine||{};if(s.mode==='PAPER_ONLY_DEVELOPMENT'){$('mode').textContent='Multi-Coin Paper · '+Object.keys(s.positions||{}).length+' Positionen · '+Object.entries(s.signals||{}).map(([k,v])=>k+':'+v).join(' · ');$('notice').textContent='PAPER ONLY · Ein gemeinsames 500-€-Testkonto, zehn Märkte, max. drei Positionen. Keine Echtgeldorders. Kurse sind Momentaufnahmen; Gebühren und Ausführung simuliert.';return;}$('mode').textContent=engine.version?'Paper v'+engine.version+' · Signal: '+(engine.signal||'—')+' · Letzte Aktion: '+(engine.last_action||'—')+(engine.safe_stop?' · SICHERHEITSSTOPP':''):'Kursbeobachtung · Paper-Handel noch nicht aktiviert.';
$('notice').textContent='Nur PAPER: keine echten Orders. Kurswerte sind stündliche Momentaufnahmen, keine Live-Ticks. Trade-Gebühren und Ausführung sind simuliert. Gewinn-Tresor ist noch nicht implementiert.';}
async function load(){try{let res=await fetch('./multi_state.json?nocache='+Date.now(),{cache:'no-store'});if(!res.ok)res=await fetch('./state.json?nocache='+Date.now(),{cache:'no-store'});if(!res.ok)throw Error('HTTP '+res.status);render(await res.json());}catch(e){$('status').textContent='● Noch keine Cloud-Verbindung';$('notice').textContent='state.json konnte nicht automatisch geladen werden. Das ist beim lokalen Öffnen einer HTML-Datei normal. Über eine Webadresse oder mit einem passenden lokalen Server kann der Abruf funktionieren. Fehler: '+e.message;}}
$('reload').onclick=load;$('coin').onchange=()=>state&&render(state);load();

async function loadResearch(){
 const status=$('research-status'),out=$('research-results');
 if(!status||!out)return;
 try{
  const response=await fetch('./research_state.json?nocache='+Date.now(),{cache:'no-store'});
  if(!response.ok)throw Error('Forschungsbericht noch nicht veröffentlicht (HTTP '+response.status+')');
  const r=await response.json();
  if(r.mode!=='RESEARCH_ONLY'||!Array.isArray(r.evolution?.ranking))throw Error('Ungültiger Forschungsbericht');
  const last=r.last_candle_utc?new Date(r.last_candle_utc).toLocaleString('de-DE'):'unbekannt';
  status.textContent='Automatische Auswertung · '+r.data_points+' XRP/EUR-Kerzen · Stand '+last;
  const core=r.intelligence_core;\n  const title=document.createElement('p');title.textContent='Intelligence Core: '+(core?.operating_mode||'FORSCHUNG')+' · '+r.evolution.ranking.length+' Strategien · '+(core?.champion===null?'Kein freigegebener Champion':'Keine automatische Handelsfreigabe')+'.';
  const list=document.createElement('ol');
  for(const s of r.evolution.ranking){
   const li=document.createElement('li');
   li.textContent=s.strategy+' · Ø Test '+Number(s.mean_oos_return_pct).toFixed(2)+' % · '+s.positive_folds+'/'+s.folds+' positive Testfenster';
   list.appendChild(li);
  }
  const extras=document.createElement('p');extras.className='muted';
  extras.textContent='Copy Trading: '+r.copy_trading.status+' · Special Situations: '+r.special_situations.status+' · Orders: '+(core?.trade_permission===false?'GESPERRT':'NICHT FREIGEGEBEN');
  const learning=document.createElement('p');learning.className='muted';\n  const history=r.learning_history;\n  learning.textContent=history?'Lernhistorie: '+history.observations+' unterschiedliche Datenstände · '+(history.status==='DESCRIPTIVE_ONLY'?'Trendbeobachtung aktiv':'noch zu wenig neue Daten'):'Lernhistorie wird eingerichtet';\n  out.replaceChildren(title,list,learning,extras);
 }catch(e){status.textContent='Automatische Forschung noch nicht verfügbar: '+e.message;out.replaceChildren()}
}
loadResearch();
