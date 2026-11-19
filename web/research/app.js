/* v2: measured results, reproducible downloads, and a focused experiment builder. */
(()=>{
'use strict';
const $=id=>document.getElementById(id), copy=x=>JSON.parse(JSON.stringify(x));
const S={catalog:null,contract:null,template:null,policy:null,cards:[],custom:null,blocked:'',spec:null,imports:[],display:new Map(),paperIds:[],addingPaper:false,customCards:[],figureViews:null};
const colors=['#087d78','#b47412','#5066aa','#ac4447','#608333','#8058a2'];
const known=x=>typeof x==='number'&&Number.isFinite(x);
const fmt=x=>known(x)?(x===0?'0':Math.abs(x)<.001?x.toExponential(3):Number(x.toPrecision(5)).toString()):'Unavailable';
const count=x=>known(x)?x.toLocaleString('en-US'):'Not reported';
function el(tag,attrs={},value){const n=document.createElement(tag);for(const[k,v]of Object.entries(attrs))n.setAttribute(k,v);if(value!=null)n.textContent=value;return n;}
function options(node,items,selected){node.replaceChildren(...items.map(([id,label])=>el('option',{value:id},label)));if(items.some(x=>x[0]===selected))node.value=selected;}
function save(name,content,type='application/json'){const url=URL.createObjectURL(content instanceof Blob?content:new Blob([content],{type}));const a=el('a',{href:url,download:name});a.click();setTimeout(()=>URL.revokeObjectURL(url),2000);}
async function digest(content){const bytes=typeof content==='string'?new TextEncoder().encode(content):content;return [...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(x=>x.toString(16).padStart(2,'0')).join('');}
async function readJSON(path){const response=await fetch(path,{cache:'no-cache'});if(!response.ok)throw Error(`${path}: HTTP ${response.status}`);return response.json();}
const record=(kind,id)=>S.catalog[kind]?.find(x=>(x[`${kind.slice(0,-1)}_id`]||x.decoder_id||x.code_id||x.circuit_id||x.dataset_id||x.experiment_id)===id);
const sourceURL=a=>a?.url&&['tracked','available','repository','tracked_summary'].includes(a.availability)?new URL(a.url.startsWith('http')?a.url:'../../'+a.url,location.href).href:null;
async function assetBytes(a){const url=sourceURL(a);if(!url)throw Error('This asset has no available repository download.');const response=await fetch(url);if(!response.ok)throw Error(`Unavailable: ${a.path}`);const bytes=new Uint8Array(await response.arrayBuffer());if(a.sha256&&await digest(bytes)!==a.sha256)throw Error(`Checksum mismatch: ${a.path}`);return bytes;}
function error(e){$('global-error').hidden=false;$('global-error').textContent=e.message||String(e);}
function route(id){if(id==='main-content'){$('main-content').focus();return;}if(!$(id)?.classList.contains('page'))id='getting-started';for(const page of document.querySelectorAll('.page'))page.hidden=page.id!==id;for(const a of document.querySelectorAll('[data-nav]')){if(a.dataset.nav===id)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');}history.replaceState(null,'','#'+id);window.scrollTo(0,0);}
function activeView(){return S.active||(S.active=ResearchCurves.active(S.catalog,S.display));}
function series(){return activeView().curves;}
const curveIdentity=s=>s.curve_id||s.series_id;
const curveForDecoder=id=>series().find(s=>evidenceMembers(s).some(m=>m.decoder_id===id));
function selected(card){return available(card).filter(s=>(card.chosen?card.chosen.has(curveIdentity(s)):!card.decoder||curveIdentity(s)===card.decoder));}
function points(card){return selected(card).filter(s=>!card.hidden.has(s.series_id)).flatMap(s=>s.points.map(p=>({s,p})));}
function bound(p){return ResearchPlot.upperBound(p);}
const metricFields={rate:'y',iterations:'mean_iterations',edge_updates:'mean_directed_edge_updates',work:'mean_work',time:'mean_seconds'};
const metricNames={iterations:'Mean iterations / shot',edge_updates:'Mean directed edge updates / shot',time:'Mean decoding time · s',work:'Mean work / shot'};
const namedWorkUnits=new Set(['iterations','BP4 iterations','BP4 sweeps','circuit DEM-BP sweeps','binary_component_sweeps','bp4_joint_sweeps','circuit_dem_bp_sweeps','directed edge updates']);
const otherWork=p=>known(p.mean_work)&&!namedWorkUnits.has(p.work_unit);
function value(card,p){return p[metricFields[card.metric]];}
function plotValue(card,p){return card.metric==='rate'&&bound(p)&&p.y===0?p.ci_high:value(card,p);}
function addPlot(){const card={id:S.cards.length?Math.max(...S.cards.map(c=>c.id))+1:1,input:S.cards.length?'b2':'a5',decoder:'',hidden:new Set(),metric:'rate'};const initial=series().find(s=>s.code_id===card.input&&s.source_decoder_id==='bp4_v2'&&s.dataset_id==='yao-vanilla-a5-b2');card.decoder=initial?curveIdentity(initial):curveIdentity(series().find(s=>s.code_id===card.input)||{})||'';S.cards.push(card);renderCards();}
function inputChoices(){const view=activeView();return [...new Map([...view.codes.map(x=>[x.code_id,x.label]),...view.circuits.map(x=>[x.circuit_id,x.comparison_label||`${x.label} · circuit`])]).entries()];}
function figureViews(){return S.figureViews||(S.figureViews=ResearchFigures.views(S.catalog,S.display));}
function figureFor(card){return card.figureId?figureViews().find(f=>f.figure_id===card.figureId):null;}
function cardInputs(card){
 const figure=figureFor(card);
 if(!card.figureId)return inputChoices();
 const ids=new Set((figure?.curves||[]).map(s=>s.circuit_id||s.code_id));
 return [['__figure__','All figure inputs'],...inputChoices().filter(([id])=>ids.has(id))];
}
const hideByDefault=(figure,curve)=>curve.paper_group==='additional'&&!figure?.guest_paper_id&&figure?.paper_id!=='mackay-0304161-v3';
function paperCard(figure,id){return {id,figureId:figure.figure_id,input:'__figure__',decoder:'',metric:'rate',
 hidden:new Set(figure.curves.filter(s=>hideByDefault(figure,s)).map(s=>s.series_id)),
 known:new Set(figure.curves.map(s=>s.series_id))};}
function reconcilePapers(){
 if(!S.paperIds.length)return;
 const availablePapers=new Set(figureViews().map(figure=>figure.paper_id));
 S.paperIds=S.paperIds.filter(id=>availablePapers.has(id));
 if(!S.paperIds.length){S.cards=S.customCards;S.addingPaper=false;return;}
 const figures=S.paperIds.flatMap(id=>figureViews().filter(f=>f.paper_id===id));
 let nextId=Math.max(0,...S.cards.map(c=>c.id))+1;
 S.cards=figures.map(figure=>{
  const card=S.cards.find(c=>c.figureId===figure.figure_id)||paperCard(figure,nextId++);
  for(const curve of figure.curves)if(!card.known.has(curve.series_id)&&hideByDefault(figure,curve))card.hidden.add(curve.series_id);
  card.known=new Set(figure.curves.map(s=>s.series_id));return card;
 });
}
function openPaper(id,additional=false){
 if(!id){
  if(S.paperIds.length)S.cards=S.customCards;
  S.paperIds=[];
 }else if(additional){
  if(!S.paperIds.includes(id))S.paperIds.push(id);
 }else if(S.paperIds[0]!==id){
  if(!S.paperIds.length){S.customCards=S.cards;S.cards=[];}
  S.paperIds=[id,...S.paperIds.slice(1).filter(paper=>paper!==id)];
 }
 S.addingPaper=false;
 renderCards();
}
function paperSearch(target,choices,select){
 target.replaceChildren();
 const wrap=el('div',{class:'curve-picker'}),label=el('label',{},'Search paper');
 const list=el('ul',{id:target.id+'-options',role:'listbox',class:'curve-options',hidden:''});
 const input=el('input',{type:'search',role:'combobox',autocomplete:'off','aria-controls':list.id,'aria-autocomplete':'list','aria-expanded':'false',placeholder:'Search by title or arXiv ID'});
 let matches=[],active=-1;
 const close=()=>{list.hidden=true;input.setAttribute('aria-expanded','false');input.removeAttribute('aria-activedescendant');active=-1;};
 const show=()=>{
  const prefix=input.value.trim().toLocaleLowerCase();
  matches=choices.filter(p=>[p.title,p.paper_id,p.source_url].some(v=>v?.toLocaleLowerCase().includes(prefix)));
  active=-1;
  input.removeAttribute('aria-activedescendant');
  list.replaceChildren(...matches.map((paper,i)=>{
   const option=el('li',{id:list.id+'-'+i,role:'option','aria-selected':'false'},paper.title);
   option.onmousedown=event=>event.preventDefault();
   option.onclick=()=>select(paper.paper_id);
   return option;
  }));
  if(!matches.length)list.append(el('li',{class:'no-match',role:'presentation'},'No matching papers.'));
  list.hidden=false;input.setAttribute('aria-expanded','true');
 };
 input.onfocus=input.oninput=show;input.onblur=close;
 input.onkeydown=event=>{
  if(event.key==='Escape'){event.preventDefault();close();}
  else if(['ArrowDown','ArrowUp'].includes(event.key)){
   event.preventDefault();if(list.hidden)show();if(!matches.length)return;
   active=active<0?(event.key==='ArrowDown'?0:matches.length-1):(active+(event.key==='ArrowDown'?1:-1)+matches.length)%matches.length;
   [...list.children].forEach((item,i)=>item.setAttribute('aria-selected',String(i===active)));
   input.setAttribute('aria-activedescendant',list.children[active].id);
   list.children[active].scrollIntoView({block:'nearest'});
  }else if(event.key==='Enter'&&!list.hidden&&matches.length&&(active>=0||matches.length===1)){
   event.preventDefault();select(matches[Math.max(active,0)].paper_id);
  }
 };
 label.append(input);wrap.append(label,list);target.append(wrap);
}
function renderPapers(){
 const ids=new Set(figureViews().map(f=>f.paper_id));
 const papers=S.catalog.papers.filter(p=>ids.has(p.paper_id));
 const remaining=papers.filter(p=>!S.paperIds.includes(p.paper_id));
 const select=$('select-paper'),additional=$('select-additional-paper');
 const choices=items=>items.map(p=>[p.paper_id,p.title]);
 options(select,[['','Custom plots'],...choices(papers)],S.paperIds[0]||'');
 select.onchange=()=>openPaper(select.value);
 paperSearch($('paper-search'),papers,id=>{openPaper(id);select.focus();});
 $('add-plot').hidden=!!S.paperIds.length;
 $('add-paper').hidden=!S.paperIds.length;
 $('add-paper').disabled=!remaining.length;
 $('add-paper').setAttribute('aria-expanded',String(S.addingPaper));
 $('paper-add-options').hidden=!S.addingPaper;
 if(S.addingPaper){
  options(additional,[['','Choose a paper'],...choices(remaining)],'');
  additional.onchange=()=>{if(additional.value){openPaper(additional.value,true);$('add-paper').focus();}};
  paperSearch($('additional-paper-search'),remaining,id=>{openPaper(id,true);$('add-paper').focus();});
 }
}
function paperSections(grid){
 return new Map(S.paperIds.map(id=>{
  const paper=record('papers',id),section=el('section',{class:'paper-section','data-paper':id,'aria-labelledby':'paper-'+id});
  const heading=el('div',{class:'section-head paper-heading'}),title=el('h3',{id:'paper-'+id},paper.title);
  if(paper.source_url)title.replaceChildren(el('a',{href:paper.source_url,target:'_blank',rel:'noopener'},paper.title));
  heading.append(title);
  if(S.paperIds.length>1){
   const remove=el('button',{type:'button',class:'secondary','aria-label':'Remove '+paper.title},'Remove paper');
   remove.onclick=()=>{S.paperIds=S.paperIds.filter(p=>p!==id);renderCards();};heading.append(remove);
  }
  section.append(heading);
  const coverage=paper.coverage;
  if(coverage?.remaining_experiments?.length){
   const label='coverage-'+id,aside=el('aside',{class:'paper-coverage','aria-labelledby':label});
   const list=el('ul');
   for(const experiment of coverage.remaining_experiments)list.append(el('li',{},experiment));
   aside.append(el('h4',{id:label},'Experiments still needed'),el('p',{},coverage.summary),list);
   section.append(aside);
  }
  grid.append(section);return[id,section];
 }));
}
function showInputPapers(target,id){
 target.replaceChildren();
 const input=record('codes',id)||record('circuits',id);
 if(!input)return;
 const ids=new Set([...(input.paper_ids||[]),...(input.source_paper_ids||[]),input.source_paper_id].filter(Boolean));
 const sources=new Set(S.catalog.result_series.filter(s=>s.code_id===id||s.circuit_id===id).map(s=>s.dataset_id));
 for(const dataset of S.catalog.datasets.filter(d=>sources.has(d.dataset_id))){
  for(const paper of dataset.paper_ids||[dataset.paper_id])ids.add(paper);
 }
 const papers=[...ids].map(paper=>record('papers',paper)).filter(paper=>paper?.source_url);
 if(!papers.length)return;
 const links=el('ul',{class:'input-sources small'});
 for(const paper of papers){const item=el('li');item.append(el('a',{href:paper.source_url,target:'_blank',rel:'noopener'},paper.title));links.append(item);}
 target.append(links);
}
function curveGroups(card){
 const wrap=el('div',{class:'curve-groups','aria-label':'Curve groups'});
 const guest=figureFor(card)?.guest_paper_id;
 for(const [id,name]of (guest?[['additional','PriorTilt Figure 1 comparisons']]:[['paper','Paper reproductions'],['additional','Additional curves']])){
  const group=available(card).filter(s=>s.paper_group===id),shown=new Set(visible(card).map(s=>s.series_id));
  const n=group.filter(s=>shown.has(s.series_id)).length;
  const label=el('label'),cb=el('input',{type:'checkbox','data-group':id,'aria-label':name});
  cb.checked=!!group.length&&n===group.length;cb.indeterminate=n>0&&n<group.length;cb.disabled=!group.length;
  cb.onchange=()=>{const show=cb.checked;card.decoder='';card.chosen=null;for(const s of group){if(show)card.hidden.delete(s.series_id);else card.hidden.add(s.series_id);}renderCards();document.querySelector(`[data-plot="${card.id}"] [data-group="${id}"]`)?.focus({preventScroll:true});};
  label.append(cb,document.createTextNode(`${name} (${group.length})`));wrap.append(label);
 }
 return wrap;
}
function reconcileCard(card){
 const inputs=cardInputs(card);
 if(!inputs.some(([id])=>id===card.input)){card.input=inputs[0]?.[0]||'';card.decoder='';card.chosen=null;card.hidden.clear();if(card.figureId)for(const s of available(card))if(hideByDefault(figureFor(card),s))card.hidden.add(s.series_id);}
 const ids=new Set(available(card).map(curveIdentity));
 card.hidden=new Set([...card.hidden].filter(id=>ids.has(id)));
 if(card.chosen){card.chosen=new Set([...card.chosen].filter(id=>ids.has(id)));if(!card.chosen.size){card.chosen=null;card.decoder='';}}
 if(card.decoder&&card.decoder!=='__selected__'&&!ids.has(card.decoder))card.decoder='';
}
function visible(card){return selected(card).filter(s=>!card.hidden.has(s.series_id));}
function available(card){const collection=card.figureId?(figureFor(card)?.curves||[]):series();return collection.filter(s=>card.figureId&&card.input==='__figure__'||s.code_id===card.input||s.circuit_id===card.input);}
function colorFor(card,s){return colors[Math.max(0,available(card).findIndex(x=>x.series_id===s.series_id))%colors.length];}
function toggleCurve(card,s){if(card.hidden.has(s.series_id))card.hidden.delete(s.series_id);else card.hidden.add(s.series_id);renderCards();const next=[...document.querySelectorAll(`[data-plot="${card.id}"] .curve-list input`)].find(n=>n.dataset.curve===s.series_id);next?.focus({preventScroll:true});}
function previewCurve(card,s,on){const box=document.querySelector(`[data-plot="${card.id}"]`);if(!box)return;const group=[...box.querySelectorAll('.curve-group')].find(g=>g.dataset.curve===s.series_id);if(group){group.classList.toggle('preview',on);group.setAttribute('opacity',on?'0.25':card.hidden.has(s.series_id)?'0':'1');}}
function curvePicker(card){
 const wrap=el('div',{class:'curve-picker'}),label=el('label',{},'Add a decoder / curve'),input=el('input',{type:'text',role:'combobox',autocomplete:'off','aria-autocomplete':'list','aria-expanded':'false','aria-controls':`curve-options-${card.id}`,'aria-label':`Add a decoder or curve to plot ${card.id}`,placeholder:'Click to list curves, or type the start of a name…'}),list=el('ul',{id:`curve-options-${card.id}`,role:'listbox',class:'curve-options',hidden:''}),status=el('span',{class:'sr-only','aria-live':'polite'});
 let matches=[],active=-1;
 const close=()=>{list.hidden=true;input.setAttribute('aria-expanded','false');input.removeAttribute('aria-activedescendant');active=-1;};
 const choose=s=>{if(!card.chosen)card.chosen=new Set(selected(card).map(curveIdentity));card.chosen.add(curveIdentity(s));card.decoder='__selected__';card.hidden.delete(s.series_id);renderCards();const next=document.querySelector(`[data-plot="${card.id}"] .curve-picker input`);next?.focus({preventScroll:true});next?.dispatchEvent(new Event('picker-close'));};
 const show=()=>{const prefix=input.value.trim().toLocaleLowerCase(),shown=new Set(visible(card).map(curveIdentity)),addable=available(card).filter(s=>!shown.has(curveIdentity(s)));matches=addable.filter(s=>s.label.toLocaleLowerCase().startsWith(prefix));list.replaceChildren();active=-1;input.removeAttribute('aria-activedescendant');for(let i=0;i<matches.length;i++){const s=matches[i],option=el('li',{role:'option',id:`curve-option-${card.id}-${i}`,'aria-selected':'false','data-decoder':s.decoder_id,'data-curve':curveIdentity(s)},s.label);option.onmousedown=e=>e.preventDefault();option.onclick=()=>choose(s);list.append(option);}if(!matches.length)list.append(el('li',{class:'no-match',role:'presentation'},addable.length?'No curve name starts with these characters.':'All available curves are already displayed.'));list.hidden=false;input.setAttribute('aria-expanded','true');status.textContent=`${matches.length} matching curves. Use arrow keys and Enter.`;};
 input.onfocus=show;input.oninput=show;input.onblur=close;input.addEventListener('picker-close',close);input.onkeydown=e=>{if(e.key==='Escape'){e.preventDefault();close();}else if(e.key==='ArrowDown'||e.key==='ArrowUp'){e.preventDefault();if(list.hidden)show();if(!matches.length)return;active=(active+(e.key==='ArrowDown'?1:-1)+matches.length)%matches.length;for(let i=0;i<list.children.length;i++)list.children[i].setAttribute('aria-selected',String(i===active));input.setAttribute('aria-activedescendant',list.children[active].id);list.children[active].scrollIntoView({block:'nearest'});}else if(e.key==='Enter'&&!list.hidden&&active>=0){e.preventDefault();choose(matches[active]);}};
 label.append(input);wrap.append(label,list,status);return wrap;
}
function parameterKey(card){const details=el('details',{class:'parameter-key'});details.append(el('summary',{},'Parameter key'));const definitions=new Map();for(const s of selected(card)){const info=S.display.get(s.source_series_id||s.series_id)||s;for(const p of info?.parameters||[])if(DecoderDisplay.symbols[p.symbol])definitions.set(p.symbol,DecoderDisplay.symbols[p.symbol]);if(info?.parameters.some(p=>p.value==='n'))definitions.set('n',DecoderDisplay.symbols.n);}const dl=el('dl');for(const [symbol,meaning]of definitions){dl.append(el('dt',{},symbol),el('dd',{},meaning));}details.append(el('p',{class:'small muted'},'SP = sum-product; MS = min-sum; OMS = offset min-sum. Every displayed parameter is followed by its value. Parameters come from the saved specification; coefficient rounding and exact numerical conventions are retained in run settings.'),dl);return details;}
function figureHeading(figure,card){
 const caption=figure?.source_caption;
 if(!caption)return el('h3',{},figure?.label||`Plot ${card.id}`);
 const heading=el('h3',{},`Figure ${caption.figure_number||figure.source_figure} `);
 const source=record('papers',figure.guest_paper_id||figure.paper_id);
 const quote=el('q',{class:'source-caption'},caption.quote);
 if(source?.source_url)quote.cite=source.source_url;
 heading.append(quote);
 if(caption.context)heading.append(document.createTextNode(' · '+caption.context));
 return heading;
}
function renderCards(){
 reconcilePapers();renderPapers();
 const grid=$('plot-grid');
 grid.classList.toggle('compare',(S.paperIds.length||S.cards.length)>1);
 grid.replaceChildren();
 const sections=paperSections(grid);
 for(const card of S.cards){
  reconcileCard(card);
  const figure=figureFor(card),container=sections.get(figure?.paper_id)||grid,box=el('article',{class:'plot-card','data-plot':card.id,...(figure?{'data-figure':figure.figure_id}:{})}),heading=el('div',{class:'card-heading'});heading.append(figureHeading(figure,card));
  if(S.cards.length>1&&!figure){const remove=el('button',{type:'button',class:'secondary','aria-label':`Remove plot ${card.id}`},'Remove');remove.onclick=()=>{S.cards=S.cards.filter(c=>c!==card);renderCards();};heading.append(remove);}box.append(heading);if(figure){box.append(el('p',{class:'small muted figure-note'},figure.note));
   const source=record('papers',figure.guest_paper_id);
   if(source)box.append(el('a',{href:source.source_url,class:'small',target:'_blank',rel:'noopener'},source.title));
  }
  const filters=el('div',{class:'selectors'});
  for(const [key,label]of [['input','Code/circuit'],['decoder','Decoder']]){const wrap=el('label',{},label),select=el('select',{'data-select':key,'aria-label':`${label} for plot ${card.id}`});const choices=key==='input'?cardInputs(card):[['','Compare available decoders'],...(card.chosen?[['__selected__','Selected curves']]:[]),...available(card).map(s=>[curveIdentity(s),s.label])];options(select,choices,card[key]);if(key==='decoder')for(const option of select.options){const item=available(card).find(s=>curveIdentity(s)===option.value);if(item)option.dataset.decoder=item.decoder_id;}select.title=choices.find(x=>x[0]===card[key])?.[1]||'';select.onchange=()=>{card[key]=select.value;card.hidden.clear();if(card.figureId)for(const s of available(card))if(hideByDefault(figureFor(card),s))card.hidden.add(s.series_id);if(key==='input'){card.chosen=null;card.decoder=card.figureId?'':available(card)[0]?curveIdentity(available(card)[0]):'';}else if(select.value!=='__selected__'){card.chosen=null;if(select.value)card.hidden.delete(select.value);}renderCards();};wrap.append(select);filters.append(wrap);}box.append(filters);
  if(!figure){const sources=el('div');showInputPapers(sources,card.input);box.append(sources);}
  const choices=selected(card);
  if(!available(card).length){box.append(el('p',{class:'empty'},'No curves with measurements at two or more error rates are available. Build a custom experiment or import measured results.'));container.append(box);continue;}
  box.append(curvePicker(card));
  const curves=el('fieldset',{class:'curves'});curves.append(el('legend',{},'Show curves'));const list=el('div',{class:'curve-list'});
  for(const s of choices){const color=colorFor(card,s),label=el('label',{style:`color:${color}`,title:s.label}),cb=el('input',{type:'checkbox','aria-label':s.label,'data-curve':s.series_id});cb.checked=!card.hidden.has(s.series_id);cb.onchange=()=>toggleCurve(card,s);const swatch=el('span',{class:'curve-swatch','aria-hidden':'true',style:`background:${color}`});label.append(cb,swatch,document.createTextNode(s.label));label.onmouseenter=()=>previewCurve(card,s,true);label.onmouseleave=()=>previewCurve(card,s,false);label.onfocusin=()=>previewCurve(card,s,true);label.onfocusout=()=>previewCurve(card,s,false);list.append(label);}curves.append(list);if(figure)curves.append(curveGroups(card));box.append(curves,parameterKey(card));
  if(figure&&!figure.guest_paper_id&&figure.paper_id!=='mackay-0304161-v3'&&!available(card).some(s=>s.paper_group==='paper'))box.append(el('p',{class:'small muted'},'Select Additional curves to show the retained controlled results.'));
  const metricLabel=el('label',{class:'metric'},'Metric'),metric=el('select',{'aria-label':`Metric for plot ${card.id}`});
  const visiblePoints=points(card),basis=visiblePoints.length?visiblePoints:choices.flatMap(s=>s.points.map(p=>({s,p})));
  const units=[...new Set(basis.filter(({p})=>otherWork(p)).map(({p})=>p.work_unit))];
  const metricChoices=[['rate','Logical / observable failure rate']];
  for(const id of ['iterations','edge_updates'])if(basis.some(({p})=>known(p[metricFields[id]])))metricChoices.push([id,metricNames[id]]);
  if(units.length===1)metricChoices.push(['work',`Mean work · ${units[0]}`]);
  if(basis.some(({p})=>known(p.mean_seconds)))metricChoices.push(['time',metricNames.time]);
  if(!metricChoices.some(x=>x[0]===card.metric))card.metric='rate';
  options(metric,metricChoices,card.metric);
  metric.onchange=()=>{card.metric=metric.value;renderCards();};
  metricLabel.append(metric);box.append(metricLabel);
  if(figure?.paper_id==='mackay-0304161-v3')drawMacKayTable(card,box);
  drawPlot(card,box);drawTable(card,box);
  const actions=el('div',{class:'actions'}),csv=el('button',{type:'button',class:'secondary'},'Export visible table');csv.disabled=!visiblePoints.length;csv.onclick=()=>exportTable(card);actions.append(csv);
  const receipt=el('button',{type:'button',class:'secondary'},'Download run settings');receipt.disabled=!visible(card).length;receipt.onclick=()=>{const shown=visible(card);save(`plot-${card.id}-settings.json`,JSON.stringify({schema:'research-plot-receipt-v2',...(figure?{paper_id:figure.paper_id,figure_id:figure.figure_id,figure_label:figure.label,reproduction_note:figure.note,paper_references:paperOverlays(card,shown)}:{}),axis:{mode:ResearchPlot.axis(shown,card.axis||'auto'),depolarizing_to_bit_flip_factor:2/3},series:shown,decoders:[...new Set(shown.flatMap(s=>evidenceMembers(s).map(m=>m.decoder_id)))].map(id=>record('decoders',id)),experiments:S.catalog.experiments.filter(e=>e.dataset_ids?.some(id=>shown.some(s=>evidenceMembers(s).some(m=>m.dataset_id===id))))},null,2)+'\n');};actions.append(receipt);
  if(visible(card).length===1){const reproduce=el('button',{type:'button',class:'secondary'},'Reproduce / extend');reproduce.onclick=()=>{const d=record('decoders',visible(card)[0].decoder_id),cfg=d.configuration||{};if(cfg.effective_policy?.schema==='vanilla-bp-decoder-v1'||cfg.experiment||cfg.portable_experiment||cfg.builder_preset||d.decoder_id==='priortilt-paper-priortilt')useSaved(d,card.input);else{const detail=box.querySelector('.run-details');detail.open=true;detail.scrollIntoView({block:'start'});}};actions.append(reproduce);}box.append(actions);runDetails(card,box);container.append(box);
 }
}
function svg(tag,attrs={},value){const n=document.createElementNS('http://www.w3.org/2000/svg',tag);for(const[k,v]of Object.entries(attrs))n.setAttribute(k,v);if(value!=null)n.textContent=value;return n;}
function paperOverlays(card,shown){
 return card.metric==='rate'?ResearchFigures.overlays(figureFor(card),shown):[];
}
function paperStar(x,y,color,description){
 const vertices=Array.from({length:10},(_,index)=>{
  const angle=index*Math.PI/5-Math.PI/2,radius=index%2?3.2:7;
  return `${x+radius*Math.cos(angle)},${y+radius*Math.sin(angle)}`;
 }).join(' ');
 const star=svg('polygon',{points:vertices,class:'paper-star',fill:color,stroke:'white',
  'stroke-width':1,'stroke-linejoin':'round',role:'img',tabindex:0,'aria-label':description});
 star.append(svg('title',{},description));return star;
}
function drawPlot(card,box){
 const curves=selected(card);
 const shown=curves.filter(s=>!card.hidden.has(s.series_id));
 const scaleCurves=shown.length?shown:curves;
 const figure=el('figure',{class:'chart'});
 const chart=svg('svg',{viewBox:'0 0 640 310',role:'group','aria-label':`Measured results for plot ${card.id}`});
 const caption=el('figcaption',{},shown.length
  ?'Click a curve to hide it; use Show curves to restore it. Hover a name to preview.'
  :'All curves are hidden. Hover or focus a curve name for a faint preview.');
 figure.append(chart,caption);
 box.append(figure);

 const log=card.metric==='rate';
 const axisMode=ResearchPlot.axis(scaleCurves,card.axis||'auto');
 const plotX=(s,p)=>ResearchPlot.coordinate(s,p,axisMode);
 const all=curves.flatMap(s=>s.points.map(p=>({s,p})));
 const scalePoints=all.filter(({s})=>!shown.length||!card.hidden.has(s.series_id));
 const activeUnits=new Set(scalePoints.filter(({p})=>known(p.mean_work)).map(({p})=>p.work_unit));
 const rows=all.filter(({p})=>{
  const y=plotValue(card,p);
  return known(p.x)&&known(y)&&(!log||y>0)
   &&(card.metric!=='work'||activeUnits.size!==1||activeUnits.has(p.work_unit));
 });
 const scaleRows=rows.filter(({s})=>!shown.length||!card.hidden.has(s.series_id));
 if(!scaleRows.length){caption.textContent='No plottable observations for this selection.';return;}

 const overlays=paperOverlays(card,shown);
 const paperRows=overlays.flatMap(reference=>{
  const s=shown.find(curve=>curve.series_id===reference.curve_id);
  return reference.points.map(p=>({s,p}));
 });
 const coordinates=[...scaleRows,...paperRows].map(({s,p})=>plotX(s,p));
 let xmin=Math.min(...coordinates),xmax=Math.max(...coordinates);
 if(xmin===xmax){xmin-=.005;xmax+=.005;}
 const values=log
  ?[...scaleRows.flatMap(({p})=>[plotValue(card,p),p.ci_low,p.ci_high].filter(v=>known(v)&&v>0)),...paperRows.map(({p})=>p.y)]
  :scaleRows.map(({p})=>plotValue(card,p));
 let ymin=Math.min(...values),ymax=Math.max(...values);
 if(log){
  ymin=Math.floor(Math.log10(ymin));
  ymax=Math.ceil(Math.log10(ymax));
  if(ymin===ymax)ymin--;
 }else if(ymin===ymax){
  ymin=0;
  ymax=ymax||1;
 }
 const left=log?64:96,right=619,top=23,bottom=258;
 const X=x=>left+(x-xmin)/(xmax-xmin)*(right-left);
 const axisY=y=>bottom-(y-ymin)/(ymax-ymin)*(bottom-top);
 const Y=y=>axisY(log?Math.log10(y):y);
 const horizontalGrid=(position,style='grid')=>{
  const y=axisY(position);
  chart.append(svg('line',{x1:left,x2:right,y1:y,y2:y,class:style}));
 };
 for(let i=0;i<=4;i++){
  const x=xmin+(xmax-xmin)*i/4;
  chart.append(svg('line',{x1:X(x),x2:X(x),y1:top,y2:bottom,class:'grid'}),
   svg('text',{x:X(x),y:279,'text-anchor':'middle',class:'x-tick'},fmt(x)));
 }
 if(log){
  for(let exponent=ymin;exponent<=ymax;exponent++){
   horizontalGrid(exponent);
   const label=svg('text',{x:left-8,y:axisY(exponent)+4,'text-anchor':'end',class:'y-tick',
    'aria-label':`10 to the power ${exponent}`},'10');
   label.append(svg('tspan',{'baseline-shift':'super','font-size':'75%'},String(exponent).replace('-','−')));
   chart.append(label);
   if(exponent===ymax)break;
   for(let multiplier=2;multiplier<=9;multiplier++){
    horizontalGrid(exponent+Math.log10(multiplier),'grid grid-minor');
   }
  }
 }else{
  for(let i=0;i<=4;i++){
   const y=ymin+(ymax-ymin)*i/4;
   horizontalGrid(y);
   const label=Math.abs(y)>=1e5?y.toExponential(2):fmt(y);
   chart.append(svg('text',{x:left-8,y:axisY(y)+4,'text-anchor':'end',class:'y-tick'},label));
  }
 }

 // A hidden curve may extend beyond the axes fitted to the displayed curves.
 const clipId=`plot-area-${card.id}`;
 const clip=svg('clipPath',{id:clipId});
 clip.append(svg('rect',{x:left,y:top,width:right-left,height:bottom-top}));
 const defs=svg('defs');
 defs.append(clip);
 chart.append(defs);
 for(const s of curves){
  const ps=rows.filter(row=>row.s===s).map(row=>row.p).sort((a,b)=>a.x-b.x);
  if(!ps.length)continue;
  const color=colorFor(card,s),hidden=card.hidden.has(s.series_id);
  const group=svg('g',{class:'curve-group','data-curve':s.series_id,'data-decoder':s.decoder_id,
   'data-visible':String(!hidden),opacity:hidden?'0':'1','aria-hidden':String(hidden),
   'pointer-events':hidden?'none':'auto'});
  if(hidden)group.setAttribute('clip-path',`url(#${clipId})`);
  const path=ResearchPlot.linePath(ps,p=>X(plotX(s,p)),p=>Y(plotValue(card,p)),p=>log&&bound(p)),line=svg('path',{d:path,stroke:color,class:'line'}),hit=svg('path',{d:path,stroke:'transparent','stroke-width':14,fill:'none',class:'curve-hit',tabindex:hidden?'-1':'0',role:'button','aria-label':`Hide curve: ${s.label}`,'aria-pressed':String(!hidden)});
  line.onclick=hit.onclick=()=>toggleCurve(card,s);hit.onkeydown=e=>{if(['Enter',' '].includes(e.key)){e.preventDefault();toggleCurve(card,s);}};hit.append(svg('title',{},`Click to hide: ${s.label}`));group.append(line,hit);
  for(const p of ps){const x=X(plotX(s,p)),y=Y(plotValue(card,p));
   if(log&&known(p.ci_high)&&p.ci_high>0&&known(p.ci_low)){
    const lower=bound(p)||p.ci_low<=0?bottom:axisY(Math.max(Math.log10(p.ci_low),ymin));
    const upper=Y(p.ci_high);
    group.append(svg('line',{class:bound(p)?'bound-error-bar':'error-bar',x1:x,x2:x,y1:lower,y2:upper,stroke:color}),svg('line',{x1:x-4,x2:x+4,y1:upper,y2:upper,stroke:color}));
    if(!bound(p))group.append(svg('line',{x1:x-4,x2:x+4,y1:lower,y2:lower,stroke:color}));
   }
   const isBound=log&&bound(p),description=`${s.label}; ${p.x_semantics==='decoder_prior_probability'?'p₀':'p'}=${fmt(p.x)}; ${isBound?'upper limit':'estimate'} ${fmt(plotValue(card,p))}; failures ${count(p.failures)}; samples ${count(p.n)}`;
   const point=isBound?svg('path',{d:`M${x-5},${y-4}L${x+5},${y-4}L${x},${y+5}Z`,fill:'white',stroke:color}):svg('circle',{cx:x,cy:y,r:4,fill:color,stroke:'white'});point.setAttribute('class','point');point.setAttribute('tabindex',hidden?'-1':'0');point.setAttribute('role','button');point.setAttribute('aria-label',description);point.append(svg('title',{},description));point.onfocus=()=>{caption.textContent=description;};point.onclick=()=>toggleCurve(card,s);point.onkeydown=e=>{if(e.key==='Enter'){e.preventDefault();caption.textContent=description;}else if(e.key===' '){e.preventDefault();toggleCurve(card,s);}};group.append(point);
  }
  chart.append(group);
 }
 for(const reference of overlays){
  const s=shown.find(curve=>curve.series_id===reference.curve_id);
  const color=colorFor(card,s);
  const source=reference.source_kind==='digitized'?'Approximate paper point, digitized from the published figure':'Paper-reported point';
  const group=svg('g',{class:'paper-markers','data-curve':s.series_id});
  for(const p of reference.points){
   const description=`${source}; ${s.label}; p=${fmt(p.x)}; ${reference.metric} ${fmt(p.y)}`;
   const star=paperStar(X(plotX(s,p)),Y(p.y),color,description);
   star.onfocus=()=>{caption.textContent=description;};
   group.append(star);
  }
  chart.append(group);
 }
 if(overlays.length)figure.append(el('p',{class:'small muted'},'★ Paper-reported points share the color of the corresponding local curve.'));
 const axisKinds=new Set(scaleRows.map(({p})=>p.x_semantics||'physical_error_probability'));const xlabel=axisMode==='bit_flip'?'Component bit-flip probability p_bit flip':axisKinds.size>1?'Probability p / p₀ (see run settings)':axisKinds.has('circuit_setting_index')?'Circuit setting index':axisKinds.has('decoder_prior_probability')?'Decoder prior probability p₀':'Physical error probability p';
 if(axisMode==='bit_flip'){const note=el('div',{class:'axis-note small'});katex.render('p_{\\mathrm{bit\\ flip}}=\\frac{2}{3}p_{\\mathrm{depolarizing}}',note,{throwOnError:true});figure.append(note,el('p',{class:'small muted'},'Depolarizing coordinates are converted automatically; X-only coordinates are unchanged. Depolarizing noise has X, Y, Z each with probability p/3. The channels remain distinct.'));}
 if(log&&scaleRows.some(({p})=>bound(p)))figure.append(el('p',{class:'small muted'},'Zero failures: the error bar runs from zero to the reported upper confidence limit. Zero is below the logarithmic plot; these bounds are not joined by a curve.'));
 chart.append(svg('text',{x:340,y:304,'text-anchor':'middle'},xlabel),svg('text',{x:16,y:144,transform:'rotate(-90 16 144)','text-anchor':'middle'},log?'Failure probability · log scale':metricNames[card.metric]));
}
const tableStart=['Series','Noise','Metric','Observed value','Samples','Failures','Type I / II','CI',metricNames.iterations,metricNames.edge_updates];
const showOtherWork=card=>points(card).some(({p})=>otherWork(p));
const showOsdWork=card=>points(card).some(({p})=>known(p.osd_invocation_fraction));
const pairedMemory=card=>points(card).some(({p})=>known(p.x_shots)&&known(p.z_shots));
const showRuntimeBudget=card=>points(card).some(({p})=>known(p.metadata?.runtime_ratio_to_bp_osd0));
function memoryBasisMeans(point,field,unit=''){
 const means=[point['x_'+field],point['z_'+field]];
 if(!means.some(known))return null;
 return means.map((mean,index)=>`${index===0?'X':'Z'} ${known(mean)?fmt(mean)+unit:'Unavailable'}`).join(' / ');
}
function headers(card){return [...tableStart,...(pairedMemory(card)?['Paper LER / cycle']:[]),...(showOtherWork(card)?['Other recorded work / shot']:[]),...(showOsdWork(card)?['OSD calls / shot','Mean OSD candidates / shot','Mean OSD time / shot']:[]),...(showRuntimeBudget(card)?['Time / BP+OSD-0']:[]),'Time','Evidence','Availability'];}
function tableRows(card){
 const paired=pairedMemory(card),includeOther=showOtherWork(card),includeOsd=showOsdWork(card),includeBudget=showRuntimeBudget(card);
 return points(card).map(({s,p})=>{
  const weighted=/importance|weighted/i.test(p.estimator||p.sampling_method||'');
  const ci=known(p.ci_low)&&known(p.ci_high)?`[${fmt(p.ci_low)}, ${fmt(p.ci_high)}]`:'Unavailable';
  const noise=p.x_semantics==='circuit_setting_index'?(p.setting_label||'Embedded circuit noise')
   :p.x_semantics==='decoder_prior_probability'?'Explicit Pauli table; p₀ = '+fmt(p.x)
   :known(p.x)?`p = ${fmt(p.x)}, ${ResearchPlot.channel(s,p)==='depolarizing'?'depolarizing (X, Y, Z: p/3 each)':ResearchPlot.channel(s,p)==='x_only'?'X-only':'circuit noise'}`:'Unavailable';
  const metric=card.metric==='rate'?(p.estimator||p.metric||(ResearchPlot.channel(s,p)==='embedded_circuit'?'Observable failure rate':'Block failure rate')):metricNames[card.metric];
  return [
   s.label,noise,metric,(bound(p)&&card.metric==='rate'?'≤ ':'')+fmt(plotValue(card,p)),
   known(p.x_shots)?`X ${count(p.x_shots)} / Z ${count(p.z_shots)}`:weighted?`${count(p.raw_samples)} raw draws`:count(p.n),
   known(p.x_errors)?`X ${count(p.x_errors)} / Z ${count(p.z_errors)}`:weighted?`${count(p.raw_failures)} raw events`:count(p.failures),
   `${count(p.type_i)} / ${count(p.type_ii)}`,
   `${ci}${known(p.confidence_level)?' · '+100*p.confidence_level+'%':''} · ${p.uncertainty_method||p.ci_method||'method not reported'}`,
   memoryBasisMeans(p,'mean_iterations',' sweeps')??(known(p.mean_iterations)?`${fmt(p.mean_iterations)} ${p.iteration_unit||'sweeps'}`:'Unavailable'),
   memoryBasisMeans(p,'mean_directed_edge_updates')??fmt(p.mean_directed_edge_updates),
   ...(paired?[fmt(p.source_value)]:[]),
   ...(includeOther?[otherWork(p)?`${fmt(p.mean_work)} ${p.work_unit}`:'Unavailable']:[]),
   ...(includeOsd?[fmt(p.osd_invocation_fraction),fmt(p.mean_osd_candidate_evaluations),known(p.mean_osd_seconds)?`${fmt(p.mean_osd_seconds)} s`:'Unavailable']:[]),
   ...(includeBudget?[known(p.metadata?.runtime_ratio_to_bp_osd0)?`${fmt(p.metadata.runtime_ratio_to_bp_osd0)}×`:'Unavailable']:[]),
   memoryBasisMeans(p,'mean_decode_ms',' ms')??(known(p.mean_seconds)?`${fmt(p.mean_seconds)} s · ${p.runtime_scope||'see run details'}`:'Unavailable'),
   `${s.evidence} · ${p.status||''}`,weighted?'Weighted estimate; proposal counts':p.raw_asset?.availability||'Retained summary',
  ];
 });
}
function drawMacKayTable(card,box){
 const rows=points(card);
 const section=el('section',{class:'mackay-results','aria-label':'Construction U block error results'});
 section.append(el('h4',{},'Block error results by decoder and noise rate'),
  el('p',{class:'small muted'},'The paper distinguishes detected and undetected classical block errors. Here the measured quantum outcomes are syndrome-inconsistent failures and syndrome-consistent logical failures.'));
 const wrap=el('div',{class:'table-wrap',tabindex:'0'}),table=el('table');
 const head=el('thead'),header=el('tr');
 for(const name of ['Decoder and code','Channel','Component bit-flip probability','Blocks tested','Total block failures','Detected (Type I)','Undetected (Type II)']){
  header.append(el('th',{scope:'col',title:name},name));
 }
 head.append(header);table.append(head);
 const body=el('tbody');
 const rate=(errors,n,estimate)=>known(errors)&&known(n)&&n>0?`${count(errors)} · ${fmt(estimate??errors/n)}`:'Unavailable';
 for(const {s,p} of rows.sort((a,b)=>a.s.label.localeCompare(b.s.label)||a.p.x-b.p.x)){
  const row=el('tr'),depolarizing=ResearchPlot.channel(s,p)==='depolarizing';
  row.append(el('th',{scope:'row',title:s.label},s.label));
  for(const val of [depolarizing?'Depolarizing':'X-only',fmt(p.x*(depolarizing?2/3:1)),count(p.n),rate(p.failures,p.n,p.y),rate(p.type_i,p.n),rate(p.type_ii,p.n)]){
   row.append(el('td',{title:val},val));
  }
  body.append(row);
 }
 table.append(body);wrap.append(table);section.append(wrap);box.append(section);
}
function drawTable(card,box){
 if(showOsdWork(card))box.append(el('p',{class:'small muted'},'Iteration and edge-update counts cover the BP stage. OSD calls, candidate evaluations and time are reported separately.'));
 if(showRuntimeBudget(card))box.append(el('p',{class:'small muted'},'Time / BP+OSD-0 compares measured decoder time per shot with the contemporaneous reference. Values above 1.1 exceed the study’s 10% runtime tolerance.'));
 if(points(card).some(({p})=>known(p.x_mean_decode_ms)||known(p.z_mean_decode_ms))){
  box.append(el('p',{class:'small muted'},'X and Z work and timing are means per shot for each memory basis. Times include decoder instrumentation and reflect the CPU allocation used for each run.'));
 }
 const wrap=el('div',{class:'table-wrap',tabindex:'0','aria-label':`Results table for plot ${card.id}`}),table=el('table'),head=el('thead'),tr=el('tr');
 const definitions={
  [metricNames.iterations]:'Executed sweeps summed across decoder components and rounds, averaged over all sampled shots.',
  [metricNames.edge_updates]:'Variable-to-check plus check-to-variable updates, averaged over all sampled shots.',
 };
 for(const heading of headers(card))tr.append(el('th',{scope:'col',...(definitions[heading]?{title:definitions[heading],class:'work-average'}:{})},heading));
 head.append(tr);table.append(head);
 const body=el('tbody');
 for(const row of tableRows(card)){
  const tr=el('tr');
  row.forEach((cell,index)=>tr.append(el('td',index===8||index===9?{class:'work-average'}:{},cell)));
  body.append(tr);
 }
 table.append(body);wrap.append(table);box.append(wrap);
}
function exportTable(card){const csv=[headers(card),...tableRows(card)].map(row=>row.map(v=>'"'+String(v).replaceAll('"','""')+'"').join(',')).join('\n')+'\n';save(`plot-${card.id}-results.csv`,csv,'text/csv');}
function evidenceMembers(s){return s.provenance_members?.length?s.provenance_members:[{series_id:s.series_id,decoder_id:s.decoder_id,dataset_id:s.dataset_id,label:s.label}];}
function runDetails(card,box){const details=el('details',{class:'run-details'});details.append(el('summary',{},'Run details and reproduction'));details.open=card.detailsOpen===true;details.ontoggle=()=>{card.detailsOpen=details.open;};const members=visible(card);if(!members.length)details.append(el('p',{class:'muted'},'No visible curves. Enable a curve to inspect its run details.'));
 for(const s of members){const section=el('div');section.append(el('h4',{},s.label));if(s.projection)section.append(el('p',{class:'small'},s.projection.rationale||`Evidence view: ${s.projection.method}.`));
  for(const member of evidenceMembers(s)){
   const d=record('datasets',member.dataset_id),decoder=record('decoders',member.decoder_id),exp=S.catalog.experiments.find(e=>e.dataset_ids?.includes(member.dataset_id));if(!d||!decoder)continue;
   const evidence=el('details',{class:'evidence-member'});evidence.append(el('summary',{},`${d.label||member.dataset_id}${member.seed!=null?', seed = '+member.seed:''}`),el('p',{},d.caveat||d.description||s.evidence));
   const config=el('details');config.append(el('summary',{},'Exact decoder settings'),el('pre',{},JSON.stringify(decoder.configuration||decoder,null,2)));evidence.append(config);
   const links=el('p'),assets=[...(d.assets||[]),decoder.asset,...s.points.map(p=>p.raw_asset).filter(Boolean)];const seen=new Set();for(const a of assets){if(!a||seen.has(a.path||a.url))continue;seen.add(a.path||a.url);const url=sourceURL(a);if(url)links.append(el('a',{href:url,target:'_blank',rel:'noopener'},a.label||a.path));else links.append(el('span',{class:'muted'},`${a.label||a.kind}: ${a.availability||'unavailable'}. `));}evidence.append(links);
   if(member.evidence_paths?.length)evidence.append(el('pre',{},member.evidence_paths.join('\n')));
   const actions=el('div',{class:'actions'}),adapt=el('button',{type:'button',class:'secondary'},'Adapt this decoder');adapt.onclick=()=>useSaved(decoder,s.code_id);actions.append(adapt);if(exp?.reproduction_recipe?.kind==='registered_study'){const original=el('button',{type:'button',class:'secondary'},'Download original experiment');original.onclick=()=>downloadOriginal(exp).catch(error);actions.append(original);}evidence.append(actions);
   if(exp?.reproduction_recipe){const recipe=el('details');recipe.append(el('summary',{},'Original run / analysis commands'),el('pre',{},JSON.stringify(exp.reproduction_recipe,null,2)));evidence.append(recipe);}section.append(evidence);
  }details.append(section);
 }details.append(el('p',{class:'muted'},'Seeds and original evidence records remain separate in the provenance. Reused cohorts count once. Unknown overlap, adaptive sampling, and importance estimates are not pooled as fixed-shot binomial observations.'));box.append(details);
}
function policyEquations(parent,expressions){
 for(const expression of expressions||[])equation(parent,typeof expression==='string'?expression:expression.latex);
}
function policies(){
 const glossary=$('policy-glossary'),target=$('policy-list');
 glossary.replaceChildren(el('h3',{},'Parameter and symbol glossary'));
 const definitions=el('dl',{class:'policy-glossary'});
 for(const item of S.policy.glossary||[]){
  const term=el('dt');
  katex.render(item.symbol,term,{throwOnError:true,trust:false});
  definitions.append(term,el('dd',{},item.meaning));
 }
 glossary.append(definitions);target.replaceChildren();
 for(const policy of S.policy.policies){
  const box=el('article',{class:'policy-card',id:'policy-'+policy.id});
  box.append(el('h3',{},policy.label));
  policyEquations(box,policy.equations);
  const params=el('div',{class:'parameters'});
  for(const parameter of policy.parameters||[]){
   const text=typeof parameter==='string'?parameter:[parameter.symbol||parameter.name,parameter.meaning||parameter.label,parameter.range].filter(Boolean).join(' · ');
   params.append(el('span',{class:'parameter'},text));
  }
  if(params.children.length)box.append(params);
  if(policy.notation){
   const symbols=el('details');
   symbols.append(el('summary',{},'Symbols'),el('p',{class:'small'},Array.isArray(policy.notation)?policy.notation.join(' · '):policy.notation));
   box.append(symbols);
  }
  if(policy.execution){
   const routes=el('details');
   routes.append(el('summary',{},'Execution routes'));
   for(const [key,route] of Object.entries(policy.execution)){
    const row=el('p',{class:'small'}),name=el('strong',{},key.replaceAll('_',' '));
    row.append(name,document.createTextNode(' · '+(route.scope||route.status)));routes.append(row);
   }
   box.append(routes);
  }
  const references=policy.literature?.length?policy.literature:policy.source_url?[{title:policy.source_label,url:policy.source_url,note:policy.source_note}]:[];
  if(references.length){
   const literature=el('details',{class:'policy-literature'});
   literature.append(el('summary',{},'Literature'));
   for(const reference of references){
    if(reference.reference)literature.append(el('p',{class:'small'},reference.reference));
    policyEquations(literature,reference.equations);
    if(reference.note)literature.append(el('p',{class:'small muted'},reference.note));
    literature.append(el('a',{href:reference.url,target:'_blank',rel:'noopener'},reference.title));
   }
   box.append(literature);
  }
  target.append(box);
 }
}
const valueOf=id=>$(id).value,num=id=>Number(valueOf(id)),optional=id=>valueOf(id).trim()===''?null:num(id);
function resetBuilder(){
 S.custom=null;S.blocked='';S.circuitMode=false;S.codeFamily='binary_css';
 $('saved-note').textContent='A new configuration creates a new experiment identity.';
 for(const input of document.querySelectorAll('#builder-form input,#builder-form select,#builder-form textarea'))input.disabled=false;
 $('builder-form').reset();
 options($('build-family'),[['binary_css','BP, binary CSS'],['bp4','Q-BP, joint Pauli']],'binary_css');
 $('build-code').value=[...$('build-code').options].some(o=>o.value==='a5')?'a5':$('build-code').options[0].value;
 $('build-preset').value='';S.pointBudgets=[];S.budgetSignature=null;
 showInputPapers($('builder-code-sources'),valueOf('build-code'));
 showInputPapers($('builder-circuit-sources'),valueOf('build-circuit'));
 $('matrix-input').open=true;
 syncBuilder();loadMatrix();preview();
}
function equation(parent,text){const node=el('div',{class:'equation'});katex.render(text,node,{displayMode:true,throwOnError:true,trust:false});parent.append(node);}
function kernelGuide(selection){
 const target=$('kernel-guide'),wasOpen=target.querySelector('details')?.open||false;
 const circuit=valueOf('build-regime')==='circuit',joint=valueOf('build-family')==='bp4';
 const controller=selection.controllers[0],controllerMinSum=['prior_tilt','relay','beam','sign_flip','mbbp'].includes(controller);
 const ms=controllerMinSum||valueOf('build-rule')==='min_sum';
 target.replaceChildren();
 const detail=el('details');detail.open=wasOpen;detail.append(el('summary',{},circuit?'Circuit BP kernel and numerical rules':joint?'Q-BP kernel and numerical rules':'BP kernel and numerical rules'));
 detail.append(el('p',{class:'small'},'A zero syndrome returns the identity correction with zero sweeps. For other syndromes the decoder tests the correction against the original checks.'));
 equation(detail,ms?String.raw`\hat m_{c\to v}^{(t+1)}=(-1)^{s_c}\!\prod_{u\in\partial c\setminus v}\!\operatorname{sgn}(m_{u\to c}^{(t)})\;\alpha\max\!\left(0,\min_{u\in\partial c\setminus v}|m_{u\to c}^{(t)}|-\beta\right)` :String.raw`\hat m_{c\to v}^{(t+1)}=2\operatorname{atanh}\!\left[(-1)^{s_c}\!\prod_{u\in\partial c\setminus v}\tanh\!\left(\frac{m_{u\to c}^{(t)}}{2}\right)\right]`);
 if(!circuit&&joint){
  equation(detail,String.raw`m_v^a=\log\frac{P_v(I)}{P_v(a)}+\sum_{c\in\partial v}A_{cv}(a)\hat m_{c\to v},\qquad a\in\{X,Y,Z\}`);
  equation(detail,String.raw`m_{v\to c}=\log\frac{\sum_{P:[P,g_{cv}]=0}\exp B_{v\to c}(P)}{\sum_{P:\{P,g_{cv}\}=0}\exp B_{v\to c}(P)}`);
  detail.append(el('p',{class:'small'},'A is 1 for anticommuting Paulis. Exclude the destination check before projection. Three identity-referenced LLRs retain a four-Pauli belief; check messages are scalar. Encoding and prior order: I, X, Y, Z. Strict Pauli decisions test I, then X, then Z using strict comparisons, otherwise choose Y.'));
 }else{
  equation(detail,String.raw`m_v=\lambda_v+\sum_{c\in\partial v}\hat m_{c\to v},\qquad m_{v\to c}=m_v-\hat m_{c\to v},\qquad\lambda_v=\log\frac{1-q_v}{q_v}`);
  detail.append(el('p',{class:'small'},circuit?'q is the independent mechanism probability from the detector error model. Corrections predict logical observables from sampled detectors.':'Separate X/Z component graphs; depolarizing priors use component probability 2p₀/3, while the physical channel remains X, Y, Z each p/3. A negative LLR selects 1; ties select 0.'));
 }
 if(controller==='prior_tilt')detail.append(el('p',{class:'small'},'PriorTilt uses min-sum with α = 1 and β = 0, and maps a zero posterior to 1.'));
 else if(controller==='mbbp')detail.append(el('p',{class:'small'},'Each declared MBBP member uses normalized min-sum with α = 0.875.'));
 else if(controllerMinSum)detail.append(el('p',{class:'small'},'The selected controller supplies the min-sum coefficients.'));
 else if(ms)detail.append(el('p',{class:'small'},`Min-sum scale α = ${valueOf('build-alpha')}, offset β = ${valueOf('build-beta')}.`));
 const policies=new Map(S.policy.policies.map(policy=>[policy.id,policy]));
 for(const id of new Set(selection.identifiers)){
  if(id==='normalized_offset_min_sum')continue;
  const policy=policies.get(id);
  if(!policy)continue;
  const block=el('section',{class:'selected-policy'});
  block.append(el('h4',{},policy.label));
  policyEquations(block,policy.equations);
  if(!policy.equations?.length&&policy.notation)block.append(el('p',{class:'small'},policy.notation));
  detail.append(block);
 }
 target.append(detail);
}
function renderPointBudgets(){
 const separate=valueOf('build-budget-mode')==='per_point',target=$('point-budgets');target.hidden=!separate;for(const node of document.querySelectorAll('.uniform-budget'))node.hidden=separate;
 if(!separate){S.budgetSignature=null;return;}const rates=valueOf('build-rates').split(',').map(p=>p.trim()).filter(Boolean),signature=JSON.stringify(rates);if(S.budgetSignature===signature&&target.children.length)return;S.budgetSignature=signature;S.pointBudgets||=[];target.replaceChildren();
 const wrap=el('div',{class:'table-wrap'}),table=el('table'),head=el('tr');for(const h of['Rate p','Shots','Total failures','Type I','Type II'])head.append(el('th',{scope:'col'},h));table.append(head);
 rates.forEach((rate,i)=>{const row=el('tr');row.append(el('th',{scope:'row'},rate));const values=S.pointBudgets[i]||(S.pointBudgets[i]={shots:optional('build-shots'),stop_failures:optional('build-failures'),stop_type_i:optional('build-type-i'),stop_type_ii:optional('build-type-ii')});for(const key of['shots','stop_failures','stop_type_i','stop_type_ii']){const td=el('td'),input=el('input',{type:'number',min:'1',placeholder:'No limit','aria-label':`${key.replaceAll('_',' ')} for p = ${rate}`,'data-budget':key,'data-rate-index':i});input.value=values[key]??'';input.oninput=()=>{values[key]=input.value.trim()===''?null:Number(input.value);preview();};td.append(input);row.append(td);}table.append(row);});wrap.append(table);target.append(wrap);
}
function syncBuilder(){
 const circuit=valueOf('build-regime')==='circuit';
 if(circuit&&!S.circuitMode){
  S.codeFamily=valueOf('build-family');
  options($('build-family'),[['circuit_dem_bp','BP, detector error model']],'circuit_dem_bp');
 }else if(!circuit&&S.circuitMode){
  options($('build-family'),[['binary_css','BP, binary CSS'],['bp4','Q-BP, joint Pauli']],S.codeFamily||'binary_css');
 }
 S.circuitMode=circuit;
 const family=valueOf('build-family'),bp4=family==='bp4',gd=valueOf('build-variant')==='guided_decimation',ms=valueOf('build-rule')==='min_sum';
 const show=(id,visible)=>{const input=$(id);input.closest('label').hidden=!visible;input.disabled=!visible;};
 $('input-legend').textContent=circuit?'Circuit':'Code';
 $('code-input').hidden=circuit;$('circuit-input').hidden=!circuit;
 $('channel-label').hidden=circuit;$('prior-label').hidden=circuit;
 $('build-family').disabled=circuit;
 $('decimation-controls').hidden=!gd;
 show('build-hard',bp4);show('build-stop',bp4&&!gd);show('build-epsilon',bp4&&gd);
 show('build-alpha',ms);show('build-beta',ms);show('build-scale',valueOf('build-format').startsWith('int'));
 const selection=ResearchBuilderPolicies.sync(S.contract,family);
 $('decoder-help').textContent=gd
  ?(bp4?'Q-BPGD uses joint Pauli beliefs.':'BPGD fixes the most reliable binary variable between BP rounds.')
  :circuit?'Circuit priors come from the detector error model.':'Binary BP uses separate X/Z components. Q-BP uses joint Pauli beliefs.';
 const all=valueOf('build-stop-mode')==='all';
 $('stopping-help').textContent=`Each rate has its own budgets. ${all?'All targets must be reached.':'Stop at the first enabled limit or target.'} ${circuit?'Circuit Type I = observable failure without detector fit. Type II = observable failure with detector fit.':'Type I = syndrome-inconsistent correction. Type II = syndrome-consistent logical failure.'}`;
 $('build-matrix').readOnly=valueOf('build-code')!=='custom';
 $('matrix-file').closest('label').hidden=$('build-matrix').readOnly;
 renderPointBudgets();kernelGuide(selection);
}
async function loadMatrix(){const id=valueOf('build-code');showInputPapers($('builder-code-sources'),id);if(id==='custom'){$('matrix-input').open=true;$('build-matrix').readOnly=false;$('matrix-note').textContent='Custom representation. Supply matrices or upload a JSON file.';return;}const code=record('codes',id);$('build-matrix').readOnly=true;$('build-matrix').value='';$('matrix-note').textContent='Loading selected check representation…';if(!code){$('matrix-note').textContent='No selected code.';return;}const asset=code.matrix_asset||code.asset||{url:'web/research/inputs/'+encodeURIComponent(id)+'.json',availability:'tracked'};
 try{const data=code.matrix_preview||JSON.parse(new TextDecoder().decode(await assetBytes(asset)));if(valueOf('build-code')!==id)return;if(!Array.isArray(data.hx)||!Array.isArray(data.hz))throw Error('The matrix preview is unavailable; the registered constructor remains the input identity.');const matrices={hx:data.hx,hz:data.hz};if(data.lx?.length&&data.lz?.length)Object.assign(matrices,{lx:data.lx,lz:data.lz});$('build-matrix').value=JSON.stringify(matrices);$('matrix-note').textContent=`${code.label}: H_X ${data.hx.length} × ${data.hx[0]?.length}, H_Z ${data.hz.length} × ${data.hz[0]?.length}. Select Custom parity check matrix to edit a new representation.`;
 }catch(e){if(valueOf('build-code')===id)$('matrix-note').textContent=e.message;}
}
function baseline(id){resetBuilder();$('build-family').value=id==='__baseline-quaternary'?'bp4':'binary_css';$('build-damping').value='0';$('build-hard').value=id==='__baseline-quaternary'?'strict_pauli':'min_llr';$('build-preset').value=id;$('saved-note').textContent='Undamped sum-product baseline, float64 v2, T = 100. Changes create a new experiment.';syncBuilder();preview();}
function chooseSaved(id){if(id.startsWith('__baseline-'))baseline(id);else{const d=record('decoders',id);if(d)useSaved(d);else resetBuilder();}}
function decoderSearch(){const target=$('decoder-search');target.replaceChildren();const wrap=el('div',{class:'curve-picker'}),label=el('label',{},'Search for a decoder'),input=el('input',{id:'build-search',role:'combobox',type:'text',autocomplete:'off','aria-autocomplete':'list','aria-expanded':'false','aria-controls':'saved-decoder-options',placeholder:'Click to list decoders, or type the start of a name…'}),list=el('ul',{id:'saved-decoder-options',class:'curve-options',role:'listbox',hidden:''});let matches=[],active=-1;
 const close=()=>{list.hidden=true;input.setAttribute('aria-expanded','false');input.removeAttribute('aria-activedescendant');};
 const show=()=>{matches=[...$('build-preset').options].filter(o=>o.value&&o.textContent.toLocaleLowerCase().startsWith(input.value.trim().toLocaleLowerCase()));active=-1;list.replaceChildren(...matches.map((o,i)=>{const node=el('li',{id:`saved-decoder-option-${i}`,role:'option','aria-selected':'false'},o.textContent);node.onmousedown=e=>e.preventDefault();node.onclick=()=>{chooseSaved(o.value);input.value=o.textContent;close();};return node;}));if(!matches.length)list.append(el('li',{class:'no-match',role:'presentation'},'No decoder name starts with these characters.'));list.hidden=false;input.setAttribute('aria-expanded','true');};
 input.onfocus=input.oninput=show;input.onblur=close;input.onkeydown=e=>{if(e.key==='Escape')close();else if(['ArrowDown','ArrowUp'].includes(e.key)){e.preventDefault();if(list.hidden)show();if(matches.length){active=(active+(e.key==='ArrowDown'?1:-1)+matches.length)%matches.length;for(let i=0;i<list.children.length;i++)list.children[i].setAttribute('aria-selected',String(i===active));input.setAttribute('aria-activedescendant',list.children[active].id);list.children[active].scrollIntoView({block:'nearest'});}}else if(e.key==='Enter'&&active>=0&&!list.hidden){e.preventDefault();chooseSaved(matches[active].value);input.value=matches[active].textContent;close();}};label.append(input);wrap.append(label,list);target.append(wrap);
}
function visualSpec(){
 const family=valueOf('build-family'),selected=ResearchBuilderPolicies.selection(S.contract,family);
 const {circuit,bp4}=selected,rule=valueOf('build-rule'),cap=num('build-iterations'),seed=num('build-seed');
 const variant=bp4&&selected.guided?'qbpgd':'plain';
 const sampling={seed,shot_start:num('build-start'),shots:optional('build-shots'),stop_failures:optional('build-failures'),stop_type_i:optional('build-type-i'),stop_type_ii:optional('build-type-ii'),stop_mode:valueOf('build-stop-mode')==='all'?'all':'any'};
 const rates=valueOf('build-rates').split(',').map(p=>p.trim());
 if(rates.some(p=>p===''))throw Error('Supply a nonempty comma-separated rate sweep.');
 if(valueOf('build-budget-mode')==='per_point')sampling.per_point=rates.map((_,i)=>({...S.pointBudgets[i]}));
 const format=valueOf('build-format');
 const overlay={
  version:'bp-flooding-policy-v1',check_rule:rule,
  resolution:{version:'bp-resolution-v1',format,scale:format.startsWith('int')?num('build-scale'):null,scope:valueOf('build-scope'),coefficients:valueOf('build-coefficients')},
  damping:num('build-damping'),alpha:rule==='min_sum'?num('build-alpha'):1,beta:rule==='min_sum'?num('build-beta'):0,
  hard_decision:bp4?valueOf('build-hard'):'min_llr',zero_syndrome_shortcut:true
 };
 const circuitRule=rule==='sum_product'?'spa':rule;
 const decoder=circuit
  ?{family,implementation:'canonical_sinter',rule:circuitRule,numerical_profile:S.contract.circuit_rule_profiles[circuitRule],schedule:'flooding',max_iterations:cap,tie_break:'zero'}
  :{family,implementation:'compiled',variant,rule,numerical_profile:bp4?'quaternary-bp4-f64-v2':'binary-spa-flooding-f64-v2',policy:overlay,schedule:'flooding',stop_on_convergence:!bp4||variant==='qbpgd'||valueOf('build-stop')==='true'};
 if(selected.controllers.length>1)throw Error('Select one decoding controller.');
 if(bp4&&!selected.guided&&selected.schedule==='variable_node_serial'&&!selected.controllers.length){
  if(overlay.damping||rule!=='sum_product'||format!=='float64')throw Error('Variable-serial Q-BP requires Sum-product, float64, and zero external damping.');
  Object.assign(decoder,{implementation:'qbp_variable_serial',numerical_profile:'quaternary-bp4-f64-v1',policy:null,stop_on_convergence:true});
 }else if(selected.controllers.includes('mbp4')){
  if(overlay.damping||rule!=='sum_product'||format!=='float64')throw Error('Fixed-alpha MBP4 requires Sum-product, float64, and zero external damping.');
  Object.assign(decoder,{implementation:'mbp4',numerical_profile:'quaternary-bp4-f64-v1',policy:null,stop_on_convergence:true,
   mbp4:{alpha:num('build-mbp4-alpha'),schedule:valueOf('build-mbp4-schedule')}});
 }else if(selected.controllers.includes('prior_tilt')){
  if(selected.memory.length||rule!=='sum_product'||overlay.damping!==0||format!=='float64')throw Error('PriorTilt supplies its own update and memory. Use Sum-product, float64, and zero external damping.');
  const text=valueOf('build-controller-options').trim();
  decoder.implementation='prior_tilt';
  decoder.prior_tilt=text?JSON.parse(text):{initial:60,round_len:6,rounds:6,ends:[],phases:[[.1,.5,.8,2]]};
  if(!circuit)decoder.policy=null;
 }else if(!bp4&&(circuit||selected.controllers.length||selected.memory.length||selected.schedule!=='flooding')){
  decoder.implementation='shared_policy';
  decoder.shared_policy=ResearchBuilderPolicies.sharedPolicy(selected,overlay,cap,String(seed));
  if(!circuit){decoder.rule='sum_product';decoder.policy=null;}
 }
 if(variant==='qbpgd')decoder.qbpgd={iterations_per_round:num('build-per-round'),epsilon:num('build-epsilon'),round_limit:num('build-rounds')};
 const code=!circuit&&(valueOf('build-code')==='custom'
  ?{kind:'embedded_css',...JSON.parse(valueOf('build-matrix'))}:{kind:'registered',id:valueOf('build-code')});
 const p0=optional('build-prior');
 return {schema:'research-experiment-v1',id:valueOf('build-id'),
  problem:circuit?{kind:'circuit',circuit:{kind:'inline_stim',text:valueOf('build-stim')},dem:{decompose_errors:false}}:{kind:bp4?'pauli_code_capacity':'css_code_capacity',code},
  channel:circuit?{kind:'embedded_circuit',noise_sweep:{source_probability:num('build-circuit-base')}}:{kind:valueOf('build-channel')},
  decoder,rate_points:circuit?rates.map(p=>({label:`p = ${Number(p)}`,physical_p:Number(p)})):rates.map(p=>({physical_p:Number(p),decoder_p0:p0===null?Number(p):p0})),
  sampling,budgets:{max_shots:null,max_iterations:cap},
  provenance:{relation:'canonical_adaptation',source_spec_id:valueOf('build-preset')||(circuit&&valueOf('build-circuit')?'circuit:'+valueOf('build-circuit'):null),notes:'New experiment; no existing performance result is inherited.'}
 };
}
function preview(){clearRequest();let inputError='';try{S.spec=S.custom?copy(S.custom):visualSpec();$('spec-preview').textContent=JSON.stringify(S.spec,null,2);}catch(e){S.spec=null;inputError=e.message;$('spec-preview').textContent=inputError;}for(const input of document.querySelectorAll('#builder-form input,#builder-form select,#builder-form textarea')){if(!['custom-spec','build-preset','build-search'].includes(input.id)&&S.custom)input.disabled=true;}for(const id of['download-package','download-json','request-results'])$(id).disabled=true;$('builder-feedback').className='muted';$('builder-feedback').textContent=S.blocked||(S.custom?'Exact saved/custom JSON mode. Visual controls are disabled; edit the JSON below or return to the visual builder to create a new configuration.':'Validate the configuration to enable downloads and result requests.');return inputError;}
function validateCurrent(){const inputError=preview();let errors=[];try{errors=S.blocked?[S.blocked]:S.spec?ResearchValidation.validate(S.spec,S.contract):[inputError||'Correct the input JSON.'];}catch(e){errors=[e.message];}const ok=!errors.length;$('builder-feedback').className=ok?'success':'error';$('builder-feedback').textContent=ok?'Configuration checked. Python repeats matrix / Stim and kernel compatibility validation before sampling.':errors.join(' ');for(const id of['download-package','download-json','request-results'])$(id).disabled=!ok;return ok;}
function useSaved(decoder,codeId){resetBuilder();$('build-preset').value=decoder.decoder_id;const config=decoder.configuration||{},policy=config.effective_policy;const request=config.experiment||decoder.experiment_spec||config.portable_experiment;
 if(request?.schema==='research-experiment-v1'){S.custom=copy(request);S.custom.id=request.id+'-edited';S.custom.provenance={relation:'canonical_adaptation',source_spec_id:decoder.decoder_id,notes:'Derived from a saved run; this is a new experiment.'};$('custom-spec').value=JSON.stringify(S.custom,null,2);}
 else if(decoder.decoder_id==='priortilt-paper-priortilt'){
  const circuit=record('circuits',codeId)||record('circuits',curveForDecoder(decoder.decoder_id)?.code_id);
  $('build-regime').value='circuit';
  $('build-controller-prior_tilt').value='on';
  $('build-damping').value='0';
  if(circuit){$('build-circuit').value=circuit.circuit_id;loadCircuit();}
 }
 else if(policy?.schema==='vanilla-bp-decoder-v1'&&['bp4','binary_css_separate'].includes(policy.family)){$('build-family').value=policy.family==='bp4'?'bp4':'binary_css';$('build-code').value=codeId||curveForDecoder(decoder.decoder_id)?.code_id||valueOf('build-code');$('build-iterations').value=policy.max_iterations;$('build-damping').value=policy.damping_old;$('build-hard').value=policy.family==='bp4'?'strict_pauli':'min_llr';}
 else S.blocked='This saved decoder has a study-specific execution path. Use Run details → Original run / analysis commands (or Download original experiment where available). Its policies cannot be substituted by a plain decoder.';
 $('saved-note').textContent=`Derived from ${curveForDecoder(decoder.decoder_id)?.label||decoder.decoder_id}. Editing creates a new experiment identity.`;syncBuilder();loadMatrix().catch(error);preview();route('builder');}
async function loadCircuit(){
 const id=valueOf('build-circuit'),item=record('circuits',id),feedback=$('circuit-feedback');
 showInputPapers($('builder-circuit-sources'),id);
 S.custom=null;S.blocked='';
 if(!item){feedback.textContent='';syncBuilder();preview();return;}
 $('build-stim').value='';
 feedback.textContent='Loading circuit…';
 try{
  let circuitText;
  if(item.asset)circuitText=new TextDecoder().decode(await assetBytes(item.asset));
  else{
   const saved=S.catalog.decoders.find(d=>d.configuration?.experiment?.problem?.kind==='circuit'&&d.configuration.experiment.problem.circuit.text&&S.catalog.result_series.some(s=>s.code_id===id&&s.decoder_id===d.decoder_id));
   if(!saved)throw Error('Circuit text is unavailable. Upload a Stim file.');
   circuitText=saved.configuration.experiment.problem.circuit.text;
  }
  if(valueOf('build-circuit')!==id)return;
  $('build-stim').value=circuitText;
  const source=item.source_probability??item.physical_p??.005;
  $('build-circuit-base').value=source;$('build-rates').value=source;
  feedback.textContent='Stim circuit loaded.';
 }catch(error){
  if(valueOf('build-circuit')!==id)return;
  feedback.textContent=error.message;
 }
 syncBuilder();preview();
}
async function portableSpec(spec){const out=copy(spec),problem=out.problem;if(problem.code?.kind==='registered'){const code=record('codes',problem.code.id),matrixAsset=code?.matrix_asset||code?.asset;if(code?.matrix_preview||matrixAsset?.path?.endsWith('.json')&&sourceURL(matrixAsset)){const data=code.matrix_preview||JSON.parse(new TextDecoder().decode(await assetBytes(matrixAsset)));if(Array.isArray(data.hx)&&Array.isArray(data.hz)){problem.code={kind:'embedded_css',hx:data.hx,hz:data.hz};if(data.lx?.length&&data.lz?.length)Object.assign(problem.code,{lx:data.lx,lz:data.lz});}}}return out;}
function clearRequest(){S.requestGeneration=(S.requestGeneration||0)+1;S.request=null;$('experiment-request').hidden=true;$('request-results').setAttribute('aria-expanded','false');$('download-request').disabled=true;$('open-request').removeAttribute('href');$('request-summary').textContent='';}
async function requestResults(){
 if(!validateCurrent())return;
 const generation=S.requestGeneration,requested=copy(S.spec),spec=await portableSpec(requested),errors=ResearchValidation.validate(spec,S.contract);
 if(errors.length)throw Error(errors.join(' '));
 const content=JSON.stringify(spec,null,2)+'\n',sha256=await digest(content);
 // An input edit during matrix loading invalidates this prepared request too.
 if(S.requestGeneration!==generation||JSON.stringify(S.spec)!==JSON.stringify(requested))return;
 const filename=spec.id.replace(/[^a-zA-Z0-9._-]/g,'-')+'-experiment.json';
 const body=[`Please run this experiment and provide its measured results.`,
  `Experiment: ${spec.id}`,`Problem: ${spec.problem.kind}`,`Decoder: ${spec.decoder.family} / ${spec.decoder.rule}`,
  `Rate points: ${spec.rate_points.length}`,`Sampling: see the attached specification for every per-point limit and stopping condition.`,
  `Attach the downloaded file: ${filename}`,`Specification SHA-256: ${sha256}`,
  'The attachment contains the complete validated experiment, including code matrices or Stim text, decoder settings, rate sweep, budgets and provenance.',
  'Requested output: manifest-bound results, event ledger and measured summaries suitable for import into the research workbench.'].join('\n\n');
 const url=new URL('https://github.com/mertgkduman/survey_bp/issues/new');url.searchParams.set('title',`Experiment results: ${spec.id}`);url.searchParams.set('body',body);
 S.request={filename,content};$('download-request').disabled=false;$('open-request').href=url.href;$('request-summary').textContent=`${spec.rate_points.length} rate point(s) · ${spec.decoder.family} · SHA-256 ${sha256}`;
 $('experiment-request').hidden=false;$('request-results').setAttribute('aria-expanded','true');$('request-heading').focus();$('builder-feedback').className='success';$('builder-feedback').textContent='Request prepared. Download the specification and attach it to your GitHub issue before submitting.';
}
async function downloadPackage(){if(!validateCurrent())return;const spec=await portableSpec(S.spec),errors=ResearchValidation.validate(spec,S.contract);if(errors.length)throw Error(errors.join(' '));const files={...S.template.files,'experiment.json':JSON.stringify(spec,null,2)+'\n','decoder.json':JSON.stringify(spec.decoder,null,2)+'\n'};if(spec.problem.code?.kind==='embedded_css'){const code={...spec.problem.code};delete code.kind;files['inputs/code.json']=JSON.stringify(code,null,2)+'\n';}if(spec.problem.circuit?.kind==='inline_stim'){files['inputs/circuit.stim']=spec.problem.circuit.text;if(spec.channel.noise_sweep)spec.rate_points.forEach((point,i)=>{files[`inputs/circuit-rate-${String(i).padStart(3,'0')}.stim`]=ResearchValidation.sweepStim(spec.problem.circuit.text,spec.channel.noise_sweep.source_probability,point.physical_p,S.contract);});const source=S.catalog.circuits.find(c=>spec.provenance.source_spec_id==='circuit:'+c.circuit_id);if(source?.asset&&await digest(spec.problem.circuit.text)===source.asset.sha256){files['inputs/circuit-source.json']=JSON.stringify({circuit_id:source.circuit_id,...source.source,circuit_sha256:source.asset.sha256},null,2)+'\n';for(const a of source.license_assets||[])files['inputs/'+a.path.split('/').pop()]=new TextDecoder().decode(await assetBytes(a));}}
 const hashes={};for(const name of Object.keys(files).sort())hashes[name]=await digest(files[name]);files['package-manifest.json']=JSON.stringify({schema:'research-package-manifest-v1',files:hashes},null,2)+'\n';save(spec.id.replace(/[^a-zA-Z0-9._-]/g,'-')+'.zip',ResearchZip.create(Object.entries(files).map(([name,content])=>({name,content}))));$('builder-feedback').textContent='Package downloaded. Extract it into a new experiment directory and run locally; see Getting started, step 3.';}
async function downloadOriginal(experiment){const files={...S.template.registered_files},recipe=experiment.reproduction_recipe,inputs={};for(const[field,label]of[['study_path','original-study'],['decoder_path','original-decoder']]){const path=recipe[field],response=await fetch('../../'+path);if(!response.ok)throw Error('Original registered input unavailable: '+path);const bytes=new Uint8Array(await response.arrayBuffer());inputs[path]=await digest(bytes);files[label+'.'+path.split('.').pop()]=new TextDecoder().decode(bytes);}files['registered-experiment.json']=JSON.stringify({schema:'registered-study-package-v1',experiment_id:experiment.experiment_id,...recipe,repository_inputs:inputs,evidence_status:experiment.evidence_status},null,2)+'\n';const hashes={};for(const name of Object.keys(files).sort())hashes[name]=await digest(files[name]);files['package-manifest.json']=JSON.stringify({schema:'research-package-manifest-v1',files:hashes},null,2)+'\n';save('original-'+experiment.experiment_id+'.zip',ResearchZip.create(Object.entries(files).map(([name,content])=>({name,content}))));}
function mergeExtension(extension){for(const kind of['papers','codes','circuits','channels','decoders','experiments','datasets','result_series']){S.catalog[kind]||=[];const idField=kind==='result_series'?'series_id':kind==='policies'?'policy_id':kind.slice(0,-1)+'_id';for(const item of extension[kind]||[]){const identifier=item[idField];if(typeof identifier!=='string'||!identifier)throw Error(`Uploaded ${kind} record has no stable identifier.`);const prior=S.catalog[kind].find(x=>x[idField]===identifier);if(prior){if(['codes','circuits'].includes(kind)&&prior.input_sha256&&prior.input_sha256===item.input_sha256)continue;if(JSON.stringify(prior)!==JSON.stringify(item))throw Error(`Conflicting imported identity: ${identifier}`);}else S.catalog[kind].push(item);}}}
async function uploadResults(files){const target=$('upload-feedback');try{target.className='muted';target.textContent='Verifying generated result files…';const {entry,summary}=await ResearchImport.read(files,S.contract);const identifier=summary.experiment_id;if(S.imports.some(x=>x.id===identifier))throw Error('This result is already saved in this browser.');const next=[...S.imports,{id:identifier,extension:entry}],previous=S.catalog;S.catalog=copy(S.catalog);try{mergeExtension(entry);localStorage.setItem('bp-research-v2-results',JSON.stringify(next));}catch(e){S.catalog=previous;throw e;}S.imports=next;fillSavedChoices();renderCards();target.className='success';target.textContent='Verified and added to this browser’s results database. Use import-results to add it to the shared repository catalog.';}catch(e){target.className='error';target.textContent=e.name==='QuotaExceededError'?'Browser storage is full. Use CLI import-results.':e.message;}}
function fillSavedChoices(){
 S.display=DecoderDisplay.labels(S.catalog);S.active=null;S.figureViews=null;const view=activeView(),current=valueOf('build-preset'),oldCode=valueOf('build-code'),oldCircuit=valueOf('build-circuit');
 options($('build-preset'),[['','Custom configuration'],['__baseline-binary','BP, SP, d = 0, T = 100, float64 v2'],['__baseline-quaternary','Q-BP, SP, d = 0, T = 100, float64 v2'],...S.catalog.decoders.filter(d=>view.decoderIds.has(d.decoder_id)).map(d=>{const s=series().find(s=>evidenceMembers(s).some(m=>m.decoder_id===d.decoder_id)),code=record('codes',s.code_id)||record('circuits',s.code_id);return[d.decoder_id,`${s.label}, code = ${code?.label||s.code_id}`];})],current);
 options($('build-code'),[...S.catalog.codes.filter(c=>S.contract.registered_code_ids.includes(c.code_id)).map(c=>[c.code_id,c.label]),['custom','Custom parity check matrix']],oldCode||'a5');
 options($('build-circuit'),[['','Custom Stim circuit'],...S.catalog.circuits.filter(c=>S.contract.registered_circuit_ids.includes(c.circuit_id)||view.circuits.includes(c)).map(c=>[c.circuit_id,c.label])],oldCircuit);
 if(oldCode&&oldCode!==valueOf('build-code')){$('build-matrix').value='';loadMatrix().catch(error);}
 if(oldCircuit&&oldCircuit!==valueOf('build-circuit'))$('build-stim').value='';
 if(current&&current!==valueOf('build-preset')){resetBuilder();$('custom-spec').value='';}
 if(S.spec){syncBuilder();preview();}
 decoderSearch();$('catalog-status').textContent=`${series().length} measured result curves · v2`;
}
function builderChange(input){
 if(input.id==='build-preset'){chooseSaved(input.value);return;}
 const family=valueOf('build-family');
 const fixedController=['prior_tilt','mbp4','relay','beam','mbbp'].some(policy=>
  input.id==='build-controller-'+policy&&input.value==='on');
 const serialPauli=input.id==='build-schedule'&&family==='bp4'&&input.value==='variable_node_serial';
 if(fixedController||serialPauli){
  $('build-rule').value='sum_product';
  $('build-format').value='float64';
  $('build-damping').value='0';
 }
 if(input.id==='build-rule'&&input.value==='min_sum'&&family==='bp4'){
  $('build-format').value='int8';
  $('build-scope').value='scalar_edges';
  $('build-hard').value='min_llr';
 }
 if(input.id==='build-variant'&&input.value==='guided_decimation'){
  $('numerical-controls').open=true;
  $('decimation-controls').open=true;
 }
 if(input.id==='build-regime'){
  S.custom=null;S.blocked='';
  if(input.value==='circuit'&&!valueOf('build-circuit'))$('build-rates').value=valueOf('build-circuit-base');
 }
 syncBuilder();preview();
}
function reportBuilderError(error){
 $('builder-feedback').className='error';
 $('builder-feedback').textContent=error.message;
}
function wire(){
 document.addEventListener('click',event=>{
  const link=event.target.closest('a[href^="#"]');
  if(link){event.preventDefault();route(link.getAttribute('href').slice(1));}
 });
 $('add-plot').onclick=addPlot;
 $('add-paper').onclick=()=>{
  S.addingPaper=!S.addingPaper;renderPapers();
  if(S.addingPaper)$('select-additional-paper').focus();
 };
 $('builder-form').onsubmit=event=>event.preventDefault();
 for(const input of document.querySelectorAll('#builder-form input,#builder-form select,#builder-form textarea')){
  if(['custom-spec','build-search'].includes(input.id))continue;
  input.addEventListener('input',()=>{
   if(input.id==='build-preset')return;
   if(input.id==='build-rates')renderPointBudgets();
   preview();
  });
  input.addEventListener('change',()=>builderChange(input));
 }
 $('build-code').addEventListener('change',()=>loadMatrix());
 $('build-circuit').addEventListener('change',()=>loadCircuit());
 $('validate-spec').onclick=validateCurrent;
 $('request-results').onclick=()=>requestResults().catch(error=>{clearRequest();reportBuilderError(error);});
 $('download-request').onclick=()=>{if(S.request)save(S.request.filename,S.request.content);};
 $('download-package').onclick=()=>downloadPackage().catch(reportBuilderError);
 $('download-json').onclick=async()=>{
  if(!validateCurrent())return;
  try{save('experiment.json',JSON.stringify(await portableSpec(S.spec),null,2)+'\n');}
  catch(error){reportBuilderError(error);}
 };
 $('apply-spec').onclick=()=>{
  try{
   const value=JSON.parse(valueOf('custom-spec')),errors=ResearchValidation.validate(value,S.contract);
   if(errors.length)throw Error(errors.join(' '));
   S.custom=value;S.blocked='';
  }catch(error){S.blocked=error.message;}
  validateCurrent();
 };
 $('reset-spec').onclick=resetBuilder;
 $('matrix-file').onchange=async event=>{
  const file=event.target.files[0];
  if(!file)return;
  $('build-matrix').value=await file.text();$('build-code').value='custom';
  syncBuilder();loadMatrix();preview();
 };
 $('stim-file').onchange=async event=>{
  const file=event.target.files[0];
  if(!file)return;
  $('build-regime').value='circuit';$('build-circuit').value='';
  $('build-stim').value=await file.text();
  loadCircuit();
 };
 $('upload-results').onchange=event=>uploadResults(event.target.files);
}
async function load(){try{[S.catalog,S.contract,S.template,S.policy]=await Promise.all([readJSON('catalog.json'),readJSON('contract.json'),readJSON('package-template.json'),readJSON('policies.json')]);const stored=JSON.parse(localStorage.getItem('bp-research-v2-results')||'[]');for(const item of stored){const previous=S.catalog;S.catalog=copy(S.catalog);try{mergeExtension(item.extension);S.imports.push(item);}catch(e){S.catalog=previous;$('upload-feedback').className='error';$('upload-feedback').textContent='A saved browser import could not be loaded: '+e.message;}}ResearchBuilderPolicies.mount(S.contract);fillSavedChoices();wire();syncBuilder();loadMatrix();preview();policies();addPlot();$('catalog-status').textContent=`${series().length} measured result curves · v2`;route(location.hash.slice(1)||'getting-started');}catch(e){error(e);}}
load();
})();
