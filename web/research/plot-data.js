/* Plot coordinates are a view of physical inputs; observations stay unchanged. */
(()=>{
'use strict';
const finite=x=>typeof x==='number'&&Number.isFinite(x);
function channel(series,point={}){return point.channel||point.metadata?.channel||series.channel_kind||series.channel||'';}
function axis(series,requested='auto'){
 const kinds=new Set(series.flatMap(s=>s.points.map(p=>channel(s,p))));
 return requested==='bit_flip'||requested==='auto'&&kinds.has('depolarizing')&&kinds.has('x_only')?'bit_flip':'physical';
}
function coordinate(series,point,mode){return mode==='bit_flip'&&channel(series,point)==='depolarizing'?2*point.x/3:point.x;}
function upperBound(point){return /bound|upper/i.test(point.status||'')||(point.is_rate_estimate===false&&/bound|upper/i.test(point.source_point_type||''))||(point.failures===0&&finite(point.ci_high));}
function linePath(points,x,y,isBound=upperBound){
 let pen=false;const parts=[];
 for(const p of points){if(isBound(p)){pen=false;continue;}parts.push(`${pen?'L':'M'}${x(p)},${y(p)}`);pen=true;}
 return parts.join(' ');
}
window.ResearchPlot={channel,axis,coordinate,upperBound,linePath};
})();
