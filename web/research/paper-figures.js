/* Figure views reuse the public evidence projection, with explicit source scope.
 * Classify retained members before projection so a cohort from another figure,
 * or a new imported decoder, cannot silently become a paper reproduction.
 */
(()=>{
'use strict';
const figureOf=p=>p.metadata?.source_figure==null?null:String(p.metadata.source_figure);
function reproduction(figure,series,point){
 return figure.reproduction_rules.some(rule=>rule.dataset_id===series.dataset_id
  &&rule.source_decoder_ids.includes(series.source_decoder_id)
  &&(rule.source_figure==null||String(rule.source_figure)===figureOf(point)));
}
function views(catalog,display){
 const datasets=new Map((catalog.datasets||[]).map(d=>[d.dataset_id,d]));
 const inputs=new Map([...catalog.codes.map(c=>[c.code_id,c.label]),...(catalog.circuits||[]).map(c=>[c.circuit_id,c.comparison_label||c.label])]);
 return (catalog.paper_figures||[]).map(figure=>{
  const members=(catalog.result_series||[]).filter(s=>{
   const d=datasets.get(s.dataset_id);
   const listed=figure.code_ids.includes(s.circuit_id||s.code_id);
   const guest=(figure.guest_rules||[]).some(rule=>rule.dataset_id===s.dataset_id&&rule.source_decoder_ids.includes(s.source_decoder_id));
   return listed&&(guest||(!figure.guest_rules?.length&&(d?.paper_ids||[d?.paper_id]).includes(figure.paper_id)));
  });
  const curves=[];
  for(const group of ['paper','additional']){
   const scoped=members.map(s=>({...s,points:s.points.filter(p=>
    // Keep the paper's explicitly conflicting figure ordinates separate.
    (figureOf(p)==null||figure.source_figure==null||figureOf(p)===String(figure.source_figure))
    &&reproduction(figure,s,p)===(group==='paper'))}));
   for(const curve of ResearchCurves.project({...catalog,result_series:scoped},display)){
    const id=curve.curve_id+'--'+figure.figure_id+'--'+group;
    curves.push({...curve,series_id:id,curve_id:id,paper_group:group,figure_id:figure.figure_id,
     label:(figure.code_ids.length>1?(inputs.get(curve.circuit_id||curve.code_id)||curve.code_id)+' · ':'')+curve.label});
   }
  }
  const original=new Map(members.map(s=>[s.series_id,s]));
  const reference_curves=(figure.reference_curves||[]).map(({matches,...reference})=>{
   const eligible=curves.filter(s=>s.code_id===reference.code_id&&s.channel_kind===reference.channel_kind);
   const curve_ids=matches.flatMap(match=>eligible.filter(s=>s.provenance_members.some(member=>{
    const source=original.get(member.series_id);
    return source?.dataset_id===match.dataset_id&&source.source_decoder_id===match.source_decoder_id;
   })).map(s=>s.series_id));
   return {...reference,curve_ids};
  });
  return {...figure,curves,reference_curves};
 }).filter(figure=>figure.curves.length);
}
function overlays(figure,curves){
 const chosen=new Set(curves.map(s=>s.series_id));
 return (figure?.reference_curves||[]).flatMap(({curve_ids,...reference})=>{
  const curve_id=curve_ids.find(id=>chosen.has(id));
  return curve_id?[{...reference,curve_id}]:[];
 });
}
globalThis.ResearchFigures={views,reproduction,overlays};
})();
