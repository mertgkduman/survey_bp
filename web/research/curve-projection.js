/* Conservative presentation projection for retained experiment evidence.
 *
 * A plot curve is an evidence view, never a new experiment identity.  The
 * projection keeps every source series reachable through provenance_members.
 * It deduplicates a point only when it has the same retained evidence path and
 * measurement key; it pools only explicitly independent fixed-IID cohorts.
 */
(()=>{
const own=(o,k)=>o!=null&&Object.prototype.hasOwnProperty.call(o,k);
const text=v=>v==null?'':String(v);
const hash=value=>{let h=2166136261;for(const c of value){h^=c.charCodeAt(0);h=Math.imul(h,16777619);}return (h>>>0).toString(16);};
const known=v=>typeof v==='number'&&Number.isFinite(v);
// Policy labels are deliberately concise.  Grouping must additionally retain
// the actual effective implementation, so two same-looking labels never get
// combined merely because a display parameter was omitted.
const stable=value=>{
 if(Array.isArray(value))return '['+value.map(stable).join(',')+']';
 if(value&&typeof value==='object')return '{'+Object.keys(value).sort().map(k=>JSON.stringify(k)+':'+stable(value[k])).join(',')+'}';
 return JSON.stringify(value);
};
const compact=value=>{
 if(Array.isArray(value)){const out=value.map(compact).filter(v=>v!==undefined);return out.length?out:undefined;}
 if(value&&typeof value==='object'){const out={};for(const [key,item] of Object.entries(value)){const child=compact(item);if(child!==undefined)out[key]=child;}return Object.keys(out).length?out:undefined;}
 return value===undefined?undefined:value;
};
const kernelFields=['kernel','family','variant','rule','check_rule','numerical_profile','message_resolution','resolution','damping_old','v2c_damping','damping_gamma','check_cap','binary_paper_v2c_cap','qbp_check_cap','product_epsilon','prior','candidate','hard_decision','stop','zero_syndrome_shortcut','max_iterations','max_iterations_per_binary_decode','alpha','alpha_schedule','first_iteration','beta','min_sum','messages','v2c','policy','qbpgd','controller','common_controls','profile_controls','arm_policy','tie_break','postprocessing','execution_backend'];
const pickKernel=value=>{
 if(!value||typeof value!=='object')return undefined;
 const profile={};for(const key of kernelFields)if(own(value,key))profile[key]=value[key];
 return compact(profile);
};
const implementationIdentity=(series,decoders)=>{
 const cfg=decoders.get(series.decoder_id)?.configuration||{};
 const effective=cfg.effective_policy||cfg.effective_configuration||cfg.effective_candidate||cfg.experiment?.decoder||cfg.portable_experiment?.decoder;
 // The profile deliberately omits labels, source paths, rate sweeps, sample
 // budgets, seeds, and output locations.  Those are evidence properties, not
 // a kernel identity.  No profile means "unknown" and is never pool-eligible.
 const profile=pickKernel(effective);
 return profile?stable(profile):'unknown_implementation';
};
const pathList=p=>text(p?.metadata?.source_evidence_path||p?.metadata?.summary_path).split(';').filter(Boolean).sort();
const member=(series,point)=>({series_id:series.series_id,decoder_id:series.decoder_id,dataset_id:series.dataset_id,label:series.label,seed:point?.metadata?.seed??null,evidence_paths:pathList(point),asset_paths:(series.assets||[]).map(a=>a.path).filter(Boolean)});
const role=p=>p?.metadata?.cohort_kind||p?.metadata?.sampling_method||p?.metadata?.estimator||p?.metadata?.source_point_type||'fixed_iid';
const evaluator=p=>p?.metadata?.denominator_definition||'retained_terminal_outcome';
const viewKey=(series,p)=>[series.code_id,series.channel_kind||'unknown',series.display_identity||series.label,series.implementation_identity||'unknown_implementation',role(p),evaluator(p),...(p.x_semantics&&p.x_semantics!=='physical_error_probability'?[p.x_semantics]:[])].join('\u001f');
const pointKey=(series,p)=>[viewKey(series,p),p.x].join('\u001f');
const evidenceKey=(series,p,index)=>{const paths=pathList(p);return paths.length?[pointKey(series,p),p.n,p.failures,p.y,paths.join(';')].join('\u001e'):`unbound:${series.series_id}:${index}`;};
const canPool=entries=>entries.length>1&&new Set(entries.map(({point})=>point.metadata?.seed)).size===entries.length&&new Set(entries.map(({point})=>pathList(point).join(';'))).size===entries.length&&entries.every(({series,point})=>series.implementation_identity!=='unknown_implementation'&&known(point.n)&&known(point.failures)&&role(point)==='fixed_iid'&&point.metadata?.seed!=null&&pathList(point).length&&point.metadata?.overlap_status!=='shared'&&point.metadata?.pooling_contract==='independent_fixed_iid_disjoint_v1');
const iterationUnits=new Set(['iterations','BP4 iterations','BP4 sweeps','circuit DEM-BP sweeps','binary_component_sweeps','bp4_joint_sweeps','circuit_dem_bp_sweeps']);
function workFields(point){
 const mean_iterations=known(point.mean_iterations)?point.mean_iterations:iterationUnits.has(point.work_unit)?point.mean_work:null;
 const mean_directed_edge_updates=known(point.mean_directed_edge_updates)?point.mean_directed_edge_updates:point.work_unit==='directed edge updates'?point.mean_work:null;
 return {...point,mean_iterations,mean_directed_edge_updates,
  iteration_unit:point.iteration_unit||(point.work_unit==='binary_component_sweeps'?'component sweeps':'sweeps')};
}
const wilson=(failures,n)=>{const z=1.959963984540054,r=failures/n,d=1+z*z/n,c=(r+z*z/(2*n))/d,h=z*Math.sqrt(r*(1-r)/n+z*z/(4*n*n))/d;return [Math.max(0,c-h),Math.min(1,c+h)];};
function pooled(entries){
 const n=entries.reduce((total,{point})=>total+point.n,0),failures=entries.reduce((total,{point})=>total+point.failures,0);
 const primary=entries[0],[ci_low,ci_high]=wilson(failures,n),sameUnit=new Set(entries.map(({point})=>point.work_unit)).size===1;
 const weighted=(field,compatible=sameUnit)=>compatible&&entries.every(({point})=>known(point[field]))?entries.reduce((sum,{point})=>sum+point[field]*point.n,0)/n:null;
 const sumCounter=field=>entries.every(({point})=>known(point[field]))?entries.reduce((sum,{point})=>sum+point[field],0):null;
 const p={...primary.point,n,failures,y:failures/n,ci_low,ci_high,mean_work:weighted('mean_work'),mean_seconds:weighted('mean_seconds'),
  mean_iterations:weighted('mean_iterations',new Set(entries.map(({point})=>point.iteration_unit)).size===1),
  mean_directed_edge_updates:weighted('mean_directed_edge_updates',true),type_i:sumCounter('type_i'),type_ii:sumCounter('type_ii'),metadata:{...primary.point.metadata,projection_members:entries.length,uncertainty_method:'wilson_score_95_percent_pooled_fixed_iid'}};
 for(const field of ['mean_bp_seconds','mean_osd_seconds','osd_invocation_fraction','mean_osd_candidate_evaluations','mean_osd_row_xor_words'])p[field]=weighted(field,true);
 return {point:p,method:'pooled_independent_fixed_iid'};
}
// The direct completion campaign supersedes these older bounded BPGD
// cohorts in the workbench. Their original catalog records remain available.
const replacedB1Arms=new Set(['bpgd_t1','bpgd_t10','bpgd_t70','bpgd_t100','bpgd_t100_r2','bpgd_t100_r5','bpgd_t100_r10','bpgd_t100_r50','bpgd_t100_r882']);
const supersededBpgd=series=>series.dataset_id==='yao-non-osd-results'
 && (series.code_id==='b1'&&replacedB1Arms.has(series.source_decoder_id)
     ||series.code_id==='c2'&&series.source_decoder_id==='bpgd_t10');
const retiredBounded=(series,point)=>supersededBpgd(series)&&role(point)==='bounded_campaign';
function projectEvidence(catalog,displayMap){
 const candidates=[];
 const decoders=new Map((catalog.decoders||[]).map(d=>[d.decoder_id,d]));
 const retiredDatasets=new Set(catalog.public_retired_dataset_ids||[]);
 const visibleDatasets=new Set((catalog.datasets||[]).filter(d=>!retiredDatasets.has(d.dataset_id)&&!['source_transcription','published_source_values'].includes(d.evidence_status)).map(d=>d.dataset_id));
 for(const source of catalog.result_series||[]){
  if(!visibleDatasets.has(source.dataset_id))continue;
  const display=displayMap?.get?.(source.series_id)||{};
  if(display.retired)continue;
  const identity=[display.algorithm||'',display.rule||'',display.precision||'',...(display.parameters||[]).filter(p=>!['N','set'].includes(p.symbol)).map(p=>p.text)].join('\u001f');
  const series={...source,label:display.label||source.label,display_identity:identity,implementation_identity:implementationIdentity(source,decoders),channel_kind:source.channel_kind||'unknown',evidence:source.evidence_status||(catalog.datasets||[]).find(d=>d.dataset_id===source.dataset_id)?.evidence_status};
  for(const [index,raw] of (source.points||[]).entries())if(!retiredBounded(source,raw)&&known(raw.x)&&known(raw.y)&&!/^pending|unmeasured|source_only/i.test(raw.status||''))candidates.push({series,point:workFields({...raw,metadata:raw.metadata||{},...(raw.metadata||{})}),index});
 }
 const grouped=new Map();
 for(const entry of candidates){const key=pointKey(entry.series,entry.point);if(!grouped.has(key))grouped.set(key,[]);grouped.get(key).push(entry);}
 const curveBuckets=new Map();
 for(const entries of grouped.values()){
  const duplicatesByEvidence=new Map();for(const entry of entries){const key=evidenceKey(entry.series,entry.point,entry.index);if(!duplicatesByEvidence.has(key))duplicatesByEvidence.set(key,[]);duplicatesByEvidence.get(key).push(entry);}
  const representatives=[...duplicatesByEvidence.values()].map(duplicates=>({primary:duplicates[0],copies:duplicates.map(x=>member(x.series,x.point)),method:duplicates.length>1?'deduplicated_reused_evidence':'single_retained_measurement'}));
  // Keep non-pooled cohorts as separate points in one curve/evidence view.
  // This deliberately does not turn different seeds, fixed budgets, or
  // selection roles into fake aggregate measurements.
  const groups=canPool(representatives.map(x=>x.primary))?[{members:representatives,method:'pooled_independent_fixed_iid'}]:representatives.map(entry=>({members:[entry],method:entry.method}));
  for(const group of groups){
   const primaries=group.members.map(x=>x.primary),primary=primaries[0],copies=group.members.flatMap(x=>x.copies);
   const result=group.method==='pooled_independent_fixed_iid'?pooled(primaries):{point:{...primary.point},method:group.method};
   result.point.provenance_members=copies;
   const s=primary.series,curveKey=viewKey(s,primary.point);
   if(!curveBuckets.has(curveKey))curveBuckets.set(curveKey,{primary:s,points:[],members:new Map(),methods:new Set()});
   const bucket=curveBuckets.get(curveKey);bucket.points.push(result.point);bucket.methods.add(result.method);for(const copy of copies)bucket.members.set(copy.series_id,copy);
  }
 }
 const projected=[...curveBuckets.values()].map(bucket=>{
  const primary=bucket.primary,points=bucket.points.sort((a,b)=>(a.x-b.x)||(a.n||0)-(b.n||0));
  const ids=[...bucket.members.keys()].sort();
  const label=primary.label;
  const display=displayMap?.get?.(primary.series_id)||{};
  const first=points[0]||{};
  const curve_id='curve-'+hash(viewKey(primary,first));
  return {...primary,...display,series_id:curve_id,source_series_id:primary.series_id,label,curve_id,points,
   provenance_members:[...bucket.members.values()],projection:{method:[...bucket.methods].sort().join('+'),source_series_ids:ids,rationale:'Retained evidence is deduplicated only by exact source membership; pooling requires distinct fixed-IID seed-tagged cohorts.'}};
 });
 // An estimator or sampling role is part of the evidence semantics, not a
 // decoder knob.  Only append it when the otherwise identical decoder view
 // would be ambiguous in the picker/legend; seeds and N never become labels.
 const labelGroups=new Map();
 for(const item of projected){const key=[item.code_id,item.channel_kind,item.label,item.implementation_identity].join('\u001f');if(!labelGroups.has(key))labelGroups.set(key,[]);labelGroups.get(key).push(item);}
 const roleLabel=point=>({pilot:'pilot',bounded_campaign:'bounded campaign',importance_sampling:'importance-weighted estimate',mixture_importance:'importance-weighted estimate'})[role(point)]||(/weighted/i.test(evaluator(point))?'weighted estimate':'separate evidence');
 for(const items of labelGroups.values())for(const item of items){
  const point=item.points[0]||{};
  if(items.length>1||supersededBpgd(item)&&point.metadata?.estimator==='mixture_importance')item.label+=`, ${roleLabel(point)}`;
 }
 return projected;
}
// This is the sole public v2 eligibility boundary. Retained catalog records
// remain untouched, including single-rate evidence and unmeasured inputs.
const hiddenInputs=new Set(['three-qubit','project-three-qubit-css-fixture']);
const measuredRate=p=>!['decoder_prior_probability','circuit_setting_index'].includes(p.x_semantics)&&known(p.x);
function project(catalog,displayMap){
 return projectEvidence(catalog,displayMap).filter(s=>!hiddenInputs.has(s.code_id)&&!hiddenInputs.has(s.circuit_id)&&new Set(s.points.filter(measuredRate).map(p=>p.x)).size>=2);
}
function active(catalog,displayMap){
 const curves=project(catalog,displayMap),inputs=new Set(curves.flatMap(s=>[s.code_id,s.circuit_id]).filter(Boolean));
 const decoderIds=new Set(curves.flatMap(s=>s.provenance_members.map(m=>m.decoder_id)));
 return {curves,codes:(catalog.codes||[]).filter(c=>inputs.has(c.code_id)&&!hiddenInputs.has(c.code_id)),circuits:(catalog.circuits||[]).filter(c=>inputs.has(c.circuit_id)&&!hiddenInputs.has(c.circuit_id)),decoderIds};
}
globalThis.ResearchCurves={project,active,projectEvidence};
})();
