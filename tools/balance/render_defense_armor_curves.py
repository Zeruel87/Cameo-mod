#!/usr/bin/env python3
"""Render the bounded armor-shape examples as an offline interactive table."""
import argparse
import html
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    if (args.out.parent/'SENT.txt').exists():
        raise SystemExit('Sent snapshot is immutable; choose a new output directory.')
    data = json.loads(args.input.read_text(encoding='utf-8'))
    embedded = json.dumps(data).replace('<', '\\u003c')
    notes = ''.join('<li>' + html.escape(n) + '</li>' for n in data['notes'])
    page = '''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Defense armor-shape comparison</title>
<style>body{font:16px system-ui;color:#202925;background:#f6f5ef;max-width:1180px;margin:32px auto;padding:0 20px}h1{font-size:30px}label{display:block;margin:20px 0 6px;font-weight:650}select,input{font:inherit;padding:8px}input[type=range]{width:min(460px,95%)}.controls{display:flex;gap:30px;flex-wrap:wrap}.scroll{overflow:auto;background:#fff;border:1px solid #d4d8ce;border-radius:8px}table{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}th,td{padding:12px;text-align:right;border-bottom:1px solid #e0e3da;white-space:nowrap}th:first-child,td:first-child{text-align:left}.mean{background:#e6efe4;font-weight:650}.warning{padding:12px;border-left:4px solid #ae6823;background:#fff2dc}.muted{color:#546259}details{margin:24px 0}li{margin:8px 0}output{font-weight:700}</style>
<h1>Defense armor-shape comparison</h1>
<p>Compare each weapon's damage across armor categories. Every source is normalized
to its own Superheavy endpoint: <b>1.0</b> means the same damage as that endpoint.
The arithmetic and geometric averages give each of the four sources 25% weight.</p>
<p class="warning">Review examples only. These are nominal HP-damage shapes, not
combat results or adopted balance values. DTA engine behavior is modeled from
reviewed source, not verified in its installed binary. No gameplay changes are made by these controls.</p>
<div class="controls"><div><label for="actor">Defense</label><select id="actor"></select></div>
<div><label for="hp">Target maximum HP in Cameo: <output id="hpvalue"></output></label>
<input id="hp" type="range" min="10000" max="1000000" step="10000" value="100000"></div>
<div><label for="blend">Explore arithmetic share: <output id="blendvalue"></output></label>
<input id="blend" type="range" min="0" max="100" step="5" value="50"></div></div>
<p class="muted">Target HP changes Cameo's percentage-damage contribution. The
blend control is an exploratory preview; no blend has been selected as policy.</p>
<p id="restriction"></p><div class="scroll"><table><thead id="head"></thead><tbody id="body"></tbody></table></div>
<details><summary>Comparison basis and limitations</summary><ul>__NOTES__</ul></details>
<script id="data" type="application/json">__DATA__</script>
<script>
const data=JSON.parse(document.getElementById('data').textContent);
const axes=['none','wood','concrete','scout','light','medium','heavy','superheavy'];
const names={ra1_soviets_flametower:'Flame Tower',ra1_soviets_teslacoil:'Tesla Coil',td_nod_obeliskoflight:'Obelisk of Light'};
const select=document.getElementById('actor');
data.rows.forEach((r,i)=>{const o=document.createElement('option');o.value=i;o.textContent=names[r.actor]||r.actor;select.append(o)});
const tr=document.createElement('tr');['Source / mean',...axes].forEach(a=>{const th=document.createElement('th');th.textContent=a;tr.append(th)});document.getElementById('head').append(tr);
function draw(){
 const row=data.rows[Number(select.value)],hp=Number(document.getElementById('hp').value),share=Number(document.getElementById('blend').value)/100;
 document.getElementById('hpvalue').textContent=hp.toLocaleString();document.getElementById('blendvalue').textContent=Math.round(share*100)+'%';
 document.getElementById('restriction').textContent=(row.additional_limitations||[]).join(' ');
 const cameo=Object.fromEntries(axes.map(a=>[a,row.cameo_terms[a].flat+hp*row.cameo_terms[a].max_hp_fraction]));
 const curves={'Current Cameo':cameo,...row.reference_nominal_curves};
 const ratios=Object.fromEntries(Object.entries(curves).map(([s,v])=>[s,axes.map(a=>v[a]/v.superheavy)]));
 const arithmetic=axes.map((a,i)=>Object.values(ratios).reduce((sum,v)=>sum+v[i],0)/4);
 const geometric=axes.map((a,i)=>{const v=Object.values(ratios).map(r=>r[i]);return v.includes(0)?0:Math.exp(v.reduce((sum,n)=>sum+Math.log(n),0)/4)});
 const records=[...Object.entries(ratios),['Arithmetic mean',arithmetic],['Geometric mean',geometric],['Exploratory blend',arithmetic.map((v,i)=>share*v+(1-share)*geometric[i])]];
 const body=document.getElementById('body');body.replaceChildren();
 records.forEach(([name,values],i)=>{const tr=document.createElement('tr');if(i>=4)tr.className='mean';const label=document.createElement('td');label.textContent=name;tr.append(label);values.forEach(v=>{const td=document.createElement('td');td.textContent=v.toFixed(3);tr.append(td)});body.append(tr)});
}
select.addEventListener('change',draw);document.getElementById('hp').addEventListener('input',draw);document.getElementById('blend').addEventListener('input',draw);draw();
</script></html>'''
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(page.replace('__DATA__', embedded).replace('__NOTES__', notes), encoding='utf-8')
    print(str(args.out))


if __name__ == '__main__':
    main()
