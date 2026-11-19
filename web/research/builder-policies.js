/* Visual controls for the canonical research experiment contract. */
(()=>{
'use strict';
const controllerDefinitions={
 relay:['RelayBP','relay_disordered_memory'],
 beam:['BeamSearch','beam_search'],
 prior_tilt:['PriorTilt','prior_tilt'],
 mbp4:['Modified BP4','modified_bp4'],
 syndrome_flip:['BP-SF','bpsf_degeneracy_cutting'],
 impulse:['Impulse decoding','impulse_decoding'],
 freezing:['Freezing','freezing'],
 sign_flip:['Sign flipping','sign_flipping'],
 restart_belief:['Restart Belief','restart_belief'],
 mbbp:['Multiple-bases BP','multiple_bases_bp']
};
const memoryDefinitions=[
 ['affine_prior','Uniform posterior memory','prior','uniform_posterior_memory',{alpha:.1}],
 ['pdprime_delta_mix','PD-prime delta mixing','belief','pdprime_delta_mix',{gamma:.5}],
 ['pdbp_field_mix','PD-BP field mixing','belief','pdbp_field_mix',{gamma:.5}],
 ['posterior_momentum','Posterior momentum','posterior','posterior_momentum',{alpha:.4,gamma:.5}]
];
const localSchedules=['layered','check_node_serial','variable_node_serial'];
const byId=id=>document.getElementById(id);
const value=id=>byId(id).value;
const number=id=>Number(value(id));
const toggle=id=>value(id)==='on';

function mount(contract){
 const host=byId('policy-controls');
 function field(title,name,tag,items){
  const wrap=document.createElement('label');
  wrap.append(title);
  const control=document.createElement(tag);
  control.id=name;
  if(items)for(const [entry,label] of items)control.add(new Option(label,entry));
  wrap.append(control);host.append(wrap);return control;
 }
 function toggleField(title,name){
  field(title,name,'select',[['off','Off'],['on','On']]);
 }
 field('Schedule','build-schedule','select',[['flooding','Flooding'],['layered','Layered'],['check_node_serial','Check-node serial'],['variable_node_serial','Variable-node serial'],['group_shuffled','Group shuffled'],['residual','Residual']]);
 field('Check partitions, JSON','build-partitions','textarea').placeholder='[[0], [1], …]';
 field('Randomized traversal','build-randomized','select',[['','Off'],['configuration','Fixed for the configuration'],['attempt','Per attempt'],['sweep','Per sweep']]);
 for(const [key,title,, ,parameters] of memoryDefinitions){
  toggleField(title,'build-memory-'+key);
  for(const [coefficient,initial] of Object.entries(parameters)){
   const input=field(title+' '+(coefficient==='alpha'?'α':'γ'),'build-memory-'+key+'-'+coefficient,'input');
   input.type='number';input.min='0';input.max='1';input.step='any';input.defaultValue=initial;
  }
 }
 for(const key of [...(contract.shared_policy_controllers||[]),'prior_tilt']){
  if(controllerDefinitions[key]&&!byId('build-controller-'+key))toggleField(controllerDefinitions[key][0],'build-controller-'+key);
 }
 if(contract.mbp4){
  toggleField('Modified BP4','build-controller-mbp4');
  const alpha=field('MBP4 α','build-mbp4-alpha','input');
  alpha.type='number';alpha.min='0.001';alpha.step='any';alpha.defaultValue='.9';
  field('MBP4 schedule','build-mbp4-schedule','select',[['qbp_flooding','Flooding'],['qbp_variable_serial','Variable-node serial']]);
 }
 const options=field('Controller parameters, JSON','build-controller-options','textarea');
 options.rows=4;
}

function selection(contract,family){
 const bp4=family==='bp4',circuit=family==='circuit_dem_bp';
 const guided=value('build-variant')==='guided_decimation';
 const controllers=Object.keys(controllerDefinitions).filter(key=>
  byId('build-controller-'+key)&&toggle('build-controller-'+key)&&
  (key==='mbp4'?Boolean(contract.mbp4)&&bp4:key==='prior_tilt'?Boolean(contract.prior_tilt)&&!bp4:(contract.shared_policy_controllers||[]).includes(key)&&!bp4));
 if(guided)controllers.unshift(bp4?'qbpgd':'guided_decimation');
 const chosenSchedule=value('build-schedule');
 const schedule=bp4&&(!contract.qbp_variable_serial||chosenSchedule!=='variable_node_serial')?'flooding':chosenSchedule;
 const memory=bp4?[]:memoryDefinitions.filter(([key])=>toggle('build-memory-'+key));
 const identifiers=[
  ...(schedule!=='flooding'?[schedule]:[]),
  ...memory.map(definition=>definition[3]),
  ...(number('build-damping')>0?['v2c_damping']:[]),
  ...(value('build-rule')==='min_sum'?['normalized_offset_min_sum']:[]),
  ...(value('build-format')!=='float64'?['message_resolution']:[]),
  ...controllers.map(key=>key==='qbpgd'?'quaternary_guided_decimation':key==='guided_decimation'?'binary_guided_decimation':controllerDefinitions[key][1])
 ];
 return {bp4,circuit,guided,controllers,schedule,memory,identifiers};
}

function sync(contract,family){
 const selected=selection(contract,family),controller=selected.controllers[0];
 const show=(id,visible)=>{const control=byId(id);if(control){control.closest('label').hidden=!visible;control.disabled=!visible;}};
 const ordinary=!selected.controllers.length;
 const scheduleControl=byId('build-schedule');
 for(const option of scheduleControl.options)option.disabled=selected.bp4&&!['flooding','variable_node_serial'].includes(option.value);
 if(scheduleControl.selectedOptions[0]?.disabled)scheduleControl.value='flooding';
 show('build-schedule',ordinary&&(!selected.bp4||Boolean(contract.qbp_variable_serial)));
 show('build-partitions',ordinary&&selected.schedule==='layered');
 show('build-randomized',ordinary&&localSchedules.includes(selected.schedule));
 for(const [key,,,,parameters] of memoryDefinitions){
  show('build-memory-'+key,!selected.bp4);
  for(const coefficient of Object.keys(parameters))show('build-memory-'+key+'-'+coefficient,!selected.bp4&&toggle('build-memory-'+key));
 }
 for(const key of Object.keys(controllerDefinitions))show('build-controller-'+key,
  key==='mbp4'?selected.bp4:!selected.bp4&&(key!=='prior_tilt'||Boolean(contract.prior_tilt)));
 show('build-mbp4-alpha',controller==='mbp4');
 show('build-mbp4-schedule',controller==='mbp4');
 show('build-controller-options',controller&&controller!=='guided_decimation'&&controller!=='qbpgd'&&controller!=='mbp4');
 const target=byId('policy-order');
 const stages=[];
 const prior=selected.memory.filter(definition=>definition[2]==='prior').map(definition=>definition[1]);
 const belief=selected.memory.filter(definition=>['belief','posterior'].includes(definition[2])).map(definition=>definition[1]);
 if(prior.length)stages.push(...prior);
 stages.push(['prior_tilt','relay','beam','sign_flip','mbbp'].includes(controller)||value('build-rule')==='min_sum'?'Min-sum check update':'Sum-product check update');
 if(belief.length)stages.push(...belief);
 if(number('build-damping')>0)stages.push('V2C damping');
 if(value('build-format')!=='float64')stages.push('Message rounding at configured update boundaries');
 if(controller)stages.push(controller==='qbpgd'?'Q-BPGD':controller==='guided_decimation'?'BPGD':controllerDefinitions[controller][0]);
 target.hidden=!selected.identifiers.length;
 target.textContent=selected.controllers.length>1?'Choose one controller for a decoder. Each controller owns the BP attempt sequence.':
  (controller?'BP update and controller order · ':'Within each sweep · ')+stages.join(' → ');
 return selected;
}

function defaultControllerOptions(controller,cap,seed){
 const short=Math.max(1,Math.min(10,Math.floor(cap/3)));
 const baseline=Math.max(2,short);
 const seeded={root_seed:seed};
 if(controller==='beam')return {};
 if(controller==='relay')return {
  legs:[{max_iterations:short},{max_iterations:short},{max_iterations:short}],
  memory_bindings:[{binding_id:'affine-prior',kind:'affine_prior',target:'prior',order:0,alpha:.1,state_lifetime:'leg'}],
  memory_tuning:{semantics:'relay_v022_dynamic_affine_prior_css_adaptation',first_leg_gamma:.1,later_leg_center:.21,later_leg_width:.9,seed_identity:seed},
  solution_limit:1,transfer:'posterior_only'
 };
 if(controller==='syndrome_flip')return {baseline_sweeps:baseline,attempt_sweeps:short,top_k:1,max_weight:1,test_cap:2,...seeded};
 if(controller==='impulse')return {realization:'exact_shortening',selection:'first_convergence',baseline_sweeps:short,attempt_sweeps:short,attempt_cap:2};
 if(controller==='freezing')return {period_sweeps:short,lifetime_sweeps:short,retry_cap:2,...seeded};
 if(controller==='sign_flip')return {alpha:.8,trunk_sweeps:short,continuation_sweeps:short};
 if(controller==='mbbp')throw Error('Enter the named row transforms and per-member budget for multiple-bases BP.');
 throw Error('Enter the controller parameters for the selected code or circuit.');
}

function sharedPolicy(selected,overlay,cap,seed){
 const controller=selected.controllers[0]||'single';
 if(selected.controllers.length>1)throw Error('Select one decoding controller.');
 if(controller!=='single'&&selected.memory.length)throw Error('Select an ordinary BP memory composition or a controller.');
 let options={};
 if(controller==='guided_decimation'){
  options={kind:'guided_decimation',variant:'algorithm1_v2_interpretation',
   source_revision:'arxiv:2312.10950v2',finite_bias_magnitude:25,
   zero_rule:'positive_prior_for_zero_posterior',final_round_rule:'return_after_last_fixation',
   round_limit:number('build-rounds'),sweeps_per_round:number('build-per-round')};
 }else if(controller!=='single'){
  const text=value('build-controller-options').trim();
  options=text?JSON.parse(text):defaultControllerOptions(controller,cap,seed);
 }
 const policy={version:'binary-policy-v1',controller,rule:'spa',schedule:'flooding',max_iterations:controller==='single'?cap:30,seed,options};
 if(controller!=='single'){
  const continuing=['guided_decimation','impulse','freezing','syndrome_flip','sign_flip','restart_belief'].includes(controller);
  if(continuing&&overlay.damping>0)policy.damping_gamma=1-overlay.damping;
  if(overlay.check_rule!=='sum_product'||overlay.resolution.format!=='float64'||(!continuing&&overlay.damping>0)){
   throw Error('This controller supplies its own check update and resolution. Select Sum-product and float64, and use the controller parameters.');
  }
  return policy;
 }
 const schedule=selected.schedule;
 policy.schedule=schedule;
 if(schedule==='layered')policy.partitions=JSON.parse(value('build-partitions'));
 if(localSchedules.includes(schedule)&&value('build-randomized'))policy.randomized=value('build-randomized');
 if(schedule==='flooding'&&!selected.memory.length){
  policy.flooding_policy={...overlay,version:'bp-flooding-policy-v2',check_stabilization:'exact_unity',product_epsilon:1e-10};
  return policy;
 }
 if(overlay.resolution.format!=='float64')throw Error('This schedule or memory composition requires float64 messages.');
 if(overlay.check_rule==='min_sum'){
  if(overlay.alpha!==1&&overlay.beta!==0)throw Error('This route supports one min-sum adjustment. Set α = 1 or β = 0.');
  policy.rule=overlay.beta>0?'offset_min_sum':overlay.alpha!==1?'normalized_min_sum':'min_sum';
  if(policy.rule!=='min_sum')policy.parameter={shape:'scalar',value:overlay.beta>0?overlay.beta:overlay.alpha};
 }
 const bindings=selected.memory.map(([key,,target,,coefficients])=>[key,target,
  Object.fromEntries(Object.keys(coefficients).map(coefficient=>[coefficient,number('build-memory-'+key+'-'+coefficient)]))]);
 if(overlay.damping)bindings.push(['v2c_damping','v2c',{gamma:1-overlay.damping}]);
 if(bindings.length)policy.memory={bindings:bindings.map(([kind,target,parameters],order)=>({
  binding_id:kind,target,kind,parameters,order,history_owner:kind,state_lifetime:'attempt',
  advance_boundary:kind==='affine_prior'||schedule==='flooding'?'source_iteration':'local_update',
  refresh_boundary:'attempt_start',source_status:'canonical_adaptation'
 }))};
 return policy;
}

globalThis.ResearchBuilderPolicies={mount,selection,sync,sharedPolicy,controllerDefinitions};
})();
