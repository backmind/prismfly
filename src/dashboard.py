"""Generate the interactive HTML dashboard with Plotly.js."""
import json
from pathlib import Path


def generate(data: dict, output: Path = Path("dashboard.html")) -> Path:
    """Generate the dashboard HTML by injecting computed data."""
    data_json = json.dumps(data)
    html = TEMPLATE.replace("__DATA__", data_json)
    output.write_text(html, encoding="utf-8")
    return output


# ── HTML Template ─────────────────────────────────────────────────
# Plotly.js loaded from CDN. All charts are interactive:
# zoom, pan, hover, toggle series in legend, range slider.

TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Real Purchasing Power</title>
<script src="https://cdn.jsdelivr.net/npm/plotly.js@2/dist/plotly.min.js"></script>
<style>
  :root{--bg:#0f172a;--card:#1e293b;--border:#334155;--text:#e2e8f0;--muted:#94a3b8;--accent:#3b82f6}
  *{margin:0;padding:0;box-sizing:border-box}
  body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:var(--bg);color:var(--text);padding:16px;line-height:1.5}
  h1{text-align:center;font-size:1.6rem;margin-bottom:4px}
  .sub{text-align:center;color:var(--muted);margin-bottom:16px;font-size:.85rem}
  .grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;max-width:1500px;margin:0 auto}
  .card{background:var(--card);border-radius:10px;padding:16px;border:1px solid var(--border)}
  .card.full{grid-column:1/-1}
  .card h2{font-size:.95rem;margin-bottom:2px}
  .card .d{font-size:.78rem;color:var(--muted);margin-bottom:8px}
  .card .d strong{color:var(--text)}
  .ctrls{display:flex;gap:8px;align-items:center;margin-bottom:8px;flex-wrap:wrap}
  .ctrls button{font-size:.75rem;padding:3px 8px;background:var(--bg);color:var(--text);border:1px solid var(--border);border-radius:4px;cursor:pointer}
  .ctrls button.a{background:var(--accent);border-color:var(--accent)}
  .note{background:var(--card);border-left:3px solid var(--accent);padding:10px 14px;margin:12px auto;max-width:1500px;border-radius:0 8px 8px 0;font-size:.8rem;color:var(--muted)}
  .note strong{color:var(--text)}.note.g{border-left-color:#22c55e}
  .kpi-row{display:flex;gap:12px;justify-content:center;margin-bottom:16px;flex-wrap:wrap}
  .kpi{background:var(--card);border-radius:8px;padding:12px 16px;text-align:center;border:1px solid var(--border);min-width:140px}
  .kpi .v{font-size:1.6rem;font-weight:bold}.kpi .l{font-size:.7rem;color:var(--muted);margin-top:2px}
  .pos{color:#4ade80}.neg{color:#f87171}.neu{color:#60a5fa}.warn{color:#fbbf24}
  table.sum{width:100%;border-collapse:collapse;font-size:.73rem}
  table.sum th{color:var(--muted);font-weight:500;padding:5px 6px;text-align:right;border-bottom:1px solid var(--border)}
  table.sum td{padding:5px 6px;text-align:right;border-bottom:1px solid #1e293b55}
  table.sum td:first-child,table.sum th:first-child{text-align:center}
  .plot{width:100%;min-height:350px}.plot-tall{width:100%;min-height:450px}
</style>
</head>
<body>
<h1>Real Purchasing Power</h1>
<p class="sub">Firefly III + Income Tax cross-analysis | Interactive dashboard</p>

<div class="note">
  <strong>Pre-2020 data</strong> may not include all shared reimbursements.
  <strong>Δ accounts</strong> = most reliable savings metric.
  Interactive charts: zoom, drag, click legend to toggle.
</div>

<div class="kpi-row" id="kpis"></div>

<div class="grid">

<div class="card full">
  <h2>Annual summary table</h2>
  <div class="d"><strong>Total deposits</strong> = all income for the year (salary + reimbursements + inheritance + other).
  <strong>Δ accounts</strong> = net change in main accounts.</div>
  <table class="sum" id="tbl"></table>
</div>

<div class="card full">
  <h2>1. Quarterly spending: necessities / discretionary / other</h2>
  <div class="d">Bars = quarterly spending. Line = quarterly salary.</div>
  <div class="ctrls"><button id="b1s" class="a" onclick="t1('stack')">Stacked</button><button id="b1g" onclick="t1('group')">Grouped</button></div>
  <div id="c1" class="plot-tall"></div>
</div>

<div class="card full">
  <h2>2. Monthly spending by basket (explorer)</h2>
  <div class="d">Use the <strong>legend</strong> to toggle. Drag to zoom. Range slider below.</div>
  <div class="ctrls"><button id="b2s" class="a" onclick="t2('stack')">Stacked</button><button id="b2g" onclick="t2('group')">Grouped</button><button id="b2r" onclick="t2('relative')">100%</button></div>
  <div id="c2" class="plot-tall"></div>
</div>

<div class="card"><h2>3. Personal inflation (PCLPI) vs CPI</h2>
  <div class="d">PCLPI = cost of necessities vs 2017. Divergence = lifestyle changes, not just prices.</div>
  <div id="c3" class="plot"></div></div>

<div class="card"><h2>4. Discretionary spending elasticity</h2>
  <div class="d">Diagonal = elasticity 1. Below diagonal = discretionary spending restraint.</div>
  <div id="c4" class="plot"></div></div>

<div class="card full"><h2>5. Heatmap: average monthly spending by basket (EUR/mo)</h2>
  <div class="d">Darker color = higher relative spending. Hover for exact values.</div>
  <div id="c5" class="plot"></div></div>

<div class="card"><h2>6. Spending distribution (%)</h2>
  <div class="d">Spending composition regardless of total.</div>
  <div id="c6" class="plot"></div></div>

<div class="card"><h2>7. Dining & leisure</h2>
  <div class="d">Bars = EUR/mo, line = % of net salary.</div>
  <div id="c7" class="plot"></div></div>

<div class="card"><h2>8. Monthly savings rate (gross)</h2>
  <div class="d">1 - (gross spending / salary).</div>
  <div id="c8" class="plot"></div></div>

<div class="card"><h2>9. Δ main accounts</h2>
  <div class="d">Net real flow in main accounts.</div>
  <div id="c9" class="plot"></div></div>

<div class="card full"><h2>10. Income composition</h2>
  <div class="d">Deposit breakdown. Click legend to filter types.</div>
  <div id="c10" class="plot"></div></div>

<div class="card full"><h2>11. Sustainability: monthly budget (steady-state)</h2>
  <div class="d">Waterfall excluding one-off renovations. Shows viability of <strong>1,000 EUR/mo</strong> investment target.</div>
  <div id="c11" class="plot-tall"></div></div>

</div>

<p class="sub" style="margin-top:16px">Auto-generated from Firefly III + income tax data</p>

<script>
const D = __DATA__;
const lo = (o={}) => ({paper_bgcolor:'#1e293b',plot_bgcolor:'#1e293b',font:{color:'#94a3b8',size:11},margin:{t:30,b:50,l:60,r:30},xaxis:{gridcolor:'#334155',...(o.xaxis||{})},yaxis:{gridcolor:'#334155',...(o.yaxis||{})},legend:{orientation:'h',y:-0.15,font:{size:10}},...o});
const cf = {responsive:true,displayModeBar:true,modeBarButtonsToRemove:['lasso2d','select2d']};

// KPIs
{const s=D.summary,last=s[s.length>1?s.length-2:0],first=s[0];
const growth=Math.round((D.fiscal[String(last.year)].neto/D.fiscal[String(first.year)].neto-1)*100);
document.getElementById('kpis').innerHTML=`
<div class="kpi"><div class="v neu">+${growth}%</div><div class="l">Salary growth<br>${first.year}→${last.year}</div></div>
<div class="kpi"><div class="v warn">x${D.c3.pclpi[D.c3.pclpi.length-2]?.toFixed(2)||'?'}</div><div class="l">PCLPI ${last.year}<br>(cost of necessities)</div></div>
<div class="kpi"><div class="v neu">x${D.c3.cpi[D.c3.cpi.length-2]?.toFixed(2)||'?'}</div><div class="l">Cumulative CPI<br>${last.year}</div></div>
<div class="kpi"><div class="v ${last.savings_rate>=0?'pos':'neg'}">${last.savings_rate>=0?'+':''}${last.savings_rate}%</div><div class="l">Savings rate ${last.year}</div></div>
<div class="kpi"><div class="v ${last.margin_mo>=0?'pos':'neg'}">${last.margin_mo>=0?'+':''}${last.margin_mo.toLocaleString()} EUR</div><div class="l">Margin/mo ${last.year}</div></div>`}

// Summary table
{const hp=D.labels.has_partner,rl=D.labels.reemb;
const rh=hp?`<th>${rl}</th>`:'';
let h=`<tr><th>Year</th><th>Months</th><th>Total deposits</th><th>Gross spending</th>${rh}<th>Net spending</th><th>Net/mo</th><th>Salary/mo</th><th>Margin/mo</th><th>Rate</th><th>Δ accounts</th></tr>`;
D.summary.forEach(r=>{const mc=r.margin_mo>=0?'pos':'neg',dc=(r.delta_accounts||0)>=0?'pos':'neg';
const rd=hp?`<td>${r.reimbursement.toLocaleString()}</td>`:'';
h+=`<tr><td>${r.year}</td><td>${r.months}</td><td>${r.total_deposits.toLocaleString()}</td><td>${r.gross_expense.toLocaleString()}</td>${rd}<td>${r.net_expense.toLocaleString()}</td><td>${r.expense_mo.toLocaleString()}</td><td>${r.salary_mo.toLocaleString()}</td><td class="${mc}">${r.margin_mo>=0?'+':''}${r.margin_mo.toLocaleString()}</td><td class="${mc}">${r.savings_rate>=0?'+':''}${r.savings_rate}%</td><td class="${dc}">${r.delta_accounts!=null?(r.delta_accounts>=0?'+':'')+r.delta_accounts.toLocaleString():'—'}</td></tr>`});
document.getElementById('tbl').innerHTML=h}

// 1. Quarterly
let m1='stack';
function d1(){Plotly.react('c1',[
{x:D.c1.quarters,y:D.c1.necessities,name:'Necessities',type:'bar',marker:{color:'#2563eb'}},
{x:D.c1.quarters,y:D.c1.discretionary,name:'Discretionary',type:'bar',marker:{color:'#9333ea'}},
{x:D.c1.quarters,y:D.c1.other,name:'Other',type:'bar',marker:{color:'#475569'}},
{x:D.c1.quarters,y:D.c1.salary,name:'Quarterly salary',type:'scatter',mode:'lines+markers',line:{color:'#4ade80',width:2,dash:'dash'},marker:{size:4}}
],lo({barmode:m1==='stack'?'stack':'group',yaxis:{gridcolor:'#334155',title:'EUR/qtr'},xaxis:{gridcolor:'#334155',tickangle:-45}}),cf)}
d1();
function t1(m){m1=m;document.getElementById('b1s').className=m==='stack'?'a':'';document.getElementById('b1g').className=m==='group'?'a':'';d1()}

// 2. Monthly
let m2='stack';
function d2(){const cs=D.baskets_order.filter(c=>D.c2[c]);
const tr=cs.map((c,i)=>({x:D.c2.months,y:D.c2[c],name:c,type:'bar',marker:{color:D.colors[i%D.colors.length]}}));
Plotly.react('c2',tr,lo({barmode:m2==='relative'?'stack':m2,barnorm:m2==='relative'?'percent':undefined,
yaxis:{gridcolor:'#334155',title:m2==='relative'?'%':'EUR/mo'},
xaxis:{gridcolor:'#334155',tickangle:-45,rangeslider:{visible:true,thickness:.06}},
legend:{orientation:'h',y:-0.25,font:{size:9}}}),cf)}
d2();
function t2(m){m2=m;['b2s','b2g','b2r'].forEach(id=>document.getElementById(id).className='');
const id=m==='stack'?'b2s':m==='group'?'b2g':'b2r';document.getElementById(id).className='a';d2()}

// 3. PCLPI vs CPI
Plotly.newPlot('c3',[
{x:D.c3.years,y:D.c3.pclpi,name:'PCLPI',mode:'lines+markers',line:{color:'#f87171'},fill:'tozeroy',fillcolor:'rgba(248,113,113,.1)'},
{x:D.c3.years,y:D.c3.cpi,name:'CPI',mode:'lines+markers',line:{color:'#60a5fa'},fill:'tozeroy',fillcolor:'rgba(96,165,250,.1)'}
],lo({yaxis:{gridcolor:'#334155',title:'Index (2017=1)'}}),cf);

// 4. Elasticity
Plotly.newPlot('c4',[
{x:D.elasticity.map(e=>e.x),y:D.elasticity.map(e=>e.y),text:D.elasticity.map(e=>e.label),mode:'markers+text',textposition:'top center',textfont:{size:9,color:'#cbd5e1'},marker:{color:'#a78bfa',size:10},name:'Year-over-year'},
{x:[-10,40],y:[-10,40],mode:'lines',line:{color:'#475569',dash:'dash'},name:'Elast.=1'}
],lo({xaxis:{gridcolor:'#334155',title:'Δ Income %',range:[-5,35]},yaxis:{gridcolor:'#334155',title:'Δ Disc. spending %',range:[-60,100]}}),cf);

// 5. Heatmap
Plotly.newPlot('c5',[{z:D.heatmap.z,x:D.heatmap.years,y:D.heatmap.baskets,type:'heatmap',
colorscale:[[0,'#1e293b'],[.5,'#2563eb'],[1,'#60a5fa']],hovertemplate:'%{y}: %{z} EUR/mo<extra></extra>'}],
lo({margin:{l:150},yaxis:{gridcolor:'#334155',autorange:'reversed'}}),cf);

// 6. Weights
{const cs=D.heatmap.baskets,yrs=D.c3.years;
const tots=yrs.map((_,i)=>D.heatmap.z.reduce((s,r)=>s+r[i],0));
Plotly.newPlot('c6',cs.map((c,ci)=>{const ri=cs.indexOf(c);return{x:yrs,y:yrs.map((_,i)=>tots[i]>0?Math.round(D.heatmap.z[ri][i]/tots[i]*1000)/10:0),name:c,type:'bar',marker:{color:D.colors[ci%D.colors.length]}}}).filter(Boolean),
lo({barmode:'stack',yaxis:{gridcolor:'#334155',title:'%',range:[0,100]},legend:{orientation:'h',y:-.2,font:{size:8}}}),cf)}

// 7. Dining & leisure
{const yrs=Object.keys(D.rest).sort();
Plotly.newPlot('c7',[
{x:yrs,y:yrs.map(y=>D.rest[y].eur),name:'EUR/mo',type:'bar',marker:{color:'#9333ea'},yaxis:'y'},
{x:yrs,y:yrs.map(y=>D.rest[y].pct),name:'% salary',type:'scatter',mode:'lines+markers',line:{color:'#f59e0b',width:2.5},marker:{size:6},yaxis:'y2'}
],lo({yaxis:{gridcolor:'#334155',title:'EUR/mo'},yaxis2:{title:'% salary',overlaying:'y',side:'right',gridcolor:'transparent'},legend:{orientation:'h',y:-.15}}),cf)}

// 8. Savings
Plotly.newPlot('c8',[
{x:D.savings.months,y:D.savings.rate,name:'Monthly',mode:'lines',line:{color:'rgba(96,165,250,.3)',width:1}},
{x:D.savings.months,y:D.savings.ma3,name:'3-mo avg',mode:'lines',line:{color:'#f59e0b',width:2}},
{x:D.savings.months,y:D.savings.months.map(()=>0),showlegend:false,mode:'lines',line:{color:'#475569',dash:'dash',width:1}}
],lo({yaxis:{gridcolor:'#334155',title:'Savings rate %'},xaxis:{gridcolor:'#334155',rangeslider:{visible:true,thickness:.08}}}),cf);

// 9. Account delta
Plotly.newPlot('c9',[{x:D.accounts_delta.years,y:D.accounts_delta.values,type:'bar',
marker:{color:D.accounts_delta.values.map(v=>v>=0?'rgba(74,222,128,.7)':'rgba(248,113,113,.7)')},
hovertemplate:'%{x}: %{y:+,} EUR<extra></extra>'}],lo({yaxis:{gridcolor:'#334155',title:'EUR/year'}}),cf);

// 10. Income
{const rp=D.labels.has_partner?`Reimbursement ${D.labels.partner}`:'Reimbursements';
const ic={Salary:'#2563eb',[rp]:'#9333ea','Tax refund':'#16a34a',Inheritance:'#f59e0b','Other income':'#64748b','Investment return':'#0d9488'};
Plotly.newPlot('c10',Object.entries(D.income.types).filter(([_,v])=>v.some(x=>x>0)).map(([t,v])=>({x:D.income.years,y:v,name:t,type:'bar',marker:{color:ic[t]||'#94a3b8'}})),
lo({barmode:'stack',yaxis:{gridcolor:'#334155',title:'EUR/year'},legend:{orientation:'h',y:-.15,font:{size:9}}}),cf)}

// 11. Waterfall
{const wf=D.waterfall;
Plotly.newPlot('c11',[{type:'waterfall',orientation:'v',
x:wf.map(w=>w.label),y:wf.map(w=>w.value),
measure:wf.map(w=>w.type==='margin'?'total':'relative'),
connector:{line:{color:'#475569',width:1}},
decreasing:{marker:{color:'#64748b'}},increasing:{marker:{color:'#4ade80'}},
totals:{marker:{color:wf[wf.length-1].value>=0?'#22c55e':'#ef4444'}},
textposition:'outside',text:wf.map(w=>(w.value>=0?'+':'')+w.value.toLocaleString()),
textfont:{size:10,color:'#cbd5e1'},
hovertemplate:'%{x}: %{y:+,} EUR<extra></extra>'}],
lo({yaxis:{gridcolor:'#334155',title:'EUR/mo'},xaxis:{gridcolor:'#334155',tickangle:-30},showlegend:false,margin:{b:120}}),cf)}
</script>
</body>
</html>"""
