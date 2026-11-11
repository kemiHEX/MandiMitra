'use client';
import {useState} from 'react';
import {ShieldCheck,Truck,Calculator} from 'lucide-react';
import {Farmer,Option,Costs,emptyCosts,Language,rupees} from '@/lib/types';
import {translations} from '@/lib/i18n';
export function FarmerForm({initial,language,onSave,busy}:{initial:Farmer;language:Language;onSave:(state:Farmer)=>void;busy:boolean}){
 const [form,setForm]=useState(initial); const t=translations(language);
 const set=(key:keyof Farmer,value:unknown)=>setForm({...form,[key]:value});
 return <form onSubmit={e=>{e.preventDefault();onSave({...form,preferred_language:language});}}>
  <div className="form-grid">
   <label>{t.crop}<select required value={form.crop||''} onChange={e=>{setForm({...form,crop:e.target.value as Farmer['crop'],crop_variety:null,grade:null});}}><option value="">{t.notSet}</option><option value="tomato">{language==='pa'?'ਟਮਾਟਰ':language==='hi'?'टमाटर':'Tomato'}</option><option value="wheat">{language==='pa'?'ਕਣਕ':language==='hi'?'गेहूँ':'Wheat'}</option><option value="potato">{language==='pa'?'ਆਲੂ':language==='hi'?'आलू':'Potato'}</option></select></label>
   <label>{t.location}<select required value={form.location||''} onChange={e=>set('location',e.target.value)}><option value="">{t.notSet}</option>{['Ludhiana','Khanna','Jagraon','Patiala','Amritsar','Jalandhar','Bathinda','Moga','Sangrur'].map(v=><option key={v}>{v}</option>)}</select></label>
   <label>{t.quantity}<div className="joined"><input required type="number" inputMode="decimal" min="0.001" max="1000000" step="0.001" value={form.quantity||''} onChange={e=>set('quantity',e.target.value||null)}/><select aria-label="Quantity unit" value={form.quantity_unit} onChange={e=>set('quantity_unit',e.target.value)}><option value="quintal">quintal</option><option value="kg">kg</option><option value="tonne">tonne</option></select></div></label>
   <label>{t.offer}<div className="joined"><span>₹</span><input required type="number" inputMode="decimal" min="0" max="100000000" step="0.01" value={form.trader_offer??''} onChange={e=>set('trader_offer',e.target.value||null)}/><select aria-label="Offer price unit" value={form.offer_unit} onChange={e=>set('offer_unit',e.target.value)}><option value="quintal">/ q</option><option value="kg">/ kg</option><option value="tonne">/ tonne</option></select></div></label>
   <label>{t.variety}<input maxLength={80} placeholder="e.g. Local" value={form.crop_variety||''} onChange={e=>set('crop_variety',e.target.value||null)}/></label>
   <label>{t.grade}<input maxLength={40} placeholder="e.g. FAQ" value={form.grade||''} onChange={e=>set('grade',e.target.value||null)}/></label>
  </div>
  <h3 className="form-subheading">{t.baseline}</h3>
  <div className="form-grid"><label>{t.traderCosts} (₹)<input required type="number" min="0" max="100000000" step="0.01" value={form.trader_costs} onChange={e=>set('trader_costs',e.target.value)}/></label><label>{t.traderLoss} (%)<input required type="number" min="0" max="99.99" step="0.01" value={form.trader_loss_percent} onChange={e=>set('trader_loss_percent',e.target.value)}/></label></div>
  <label className="check"><input type="checkbox" checked={form.baseline_confirmed} onChange={e=>set('baseline_confirmed',e.target.checked)}/><span>{t.confirmTrader}</span></label>
  <div className="notice"><ShieldCheck size={18}/><span>{t.noProfit}</span></div>
  <button className="button primary full" disabled={busy}>{t.apply}</button>
 </form>;
}
export function CostForm({option,language,onSave,busy}:{option:Option;language:Language;onSave:(costs:Costs)=>void;busy:boolean}){
 const [costs,setCosts]=useState<Costs>(option.costs||emptyCosts); const t=translations(language);
 const fields:[keyof Costs,string,string][]=[['transport',t.transport,'₹'],['loading',t.loading,'₹'],['other',t.other,'₹'],['market_fee_percent',t.fee,'%'],['loss_percent',t.loss,'%']];
 return <form onSubmit={e=>{e.preventDefault();onSave(costs);}}><div className="notice"><Truck size={20}/><span>{t.reviewEstimate}. {language==='en'?'These are your estimates, not transport quotes. Fees are a percentage of gross proceeds.':''}</span></div><div className="form-grid">{fields.map(([key,label,unit])=><label key={key}>{label} ({unit})<input required type="number" inputMode="decimal" min="0" max={key==='loss_percent'?'99.99':key==='market_fee_percent'?'30':'100000000'} step="0.01" value={String(costs[key])} onChange={e=>setCosts({...costs,[key]:e.target.value})}/></label>)}</div><label className="check"><input required type="checkbox" checked={costs.confirmed} onChange={e=>setCosts({...costs,confirmed:e.target.checked})}/><span>{t.confirmCosts}</span></label><button className="button primary full" disabled={busy}><Calculator size={18}/>{t.update}</button></form>;
}
export function Calculation({option,language}:{option:Option;language:Language}){
 const t=translations(language); if(option.status!=='calculated')return null;
 return <div className="calculation"><h3>{t.formula}</h3><div className="formula">{Number(option.saleable_quantity).toLocaleString('en-IN')} q × {rupees(option.observation.modal_price)} − {rupees(option.total_costs)} = <strong>{rupees(option.net)}</strong></div><dl><div><dt>{t.saleable}</dt><dd>{Number(option.saleable_quantity).toLocaleString('en-IN')} q</dd></div><div><dt>{t.gross}</dt><dd>{rupees(option.gross)}</dd></div><div><dt>{t.transport}</dt><dd>− {rupees(option.costs?.transport)}</dd></div><div><dt>{t.loading}</dt><dd>− {rupees(option.costs?.loading)}</dd></div><div><dt>{t.other}</dt><dd>− {rupees(option.costs?.other)}</dd></div><div><dt>{t.fee} ({option.costs?.market_fee_percent}%)</dt><dd>− {rupees(option.market_fees)}</dd></div><div><dt>{t.total}</dt><dd>− {rupees(option.total_costs)}</dd></div><div className="sum"><dt>{t.net}</dt><dd>{rupees(option.net)}</dd></div><div><dt>{t.breakEven}</dt><dd>{rupees(option.break_even)} / q</dd></div></dl><h3>{t.sensitivity}</h3><p className="muted small">{t.hypothetical}</p><div className="sensitivity">{option.sensitivity?.map((r,i)=><div key={r.price}><span>{i===0?'−10%':i===1?t.modal:'+10%'}</span><b>{rupees(r.price)} / q</b><strong>{rupees(r.net)}</strong><small>{t.net}</small></div>)}</div></div>;
}
