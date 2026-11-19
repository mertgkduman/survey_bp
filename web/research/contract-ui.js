/* Browser guidance from shared Python contract; Python remains authoritative. */
(()=>{
const known=v=>typeof v==="number"&&Number.isFinite(v);
  function matrix(value, name) {
    if (!Array.isArray(value) || !value.length || !Array.isArray(value[0]) || !value[0].length || value.some(row => !Array.isArray(row) || row.length !== value[0].length || row.some(bit => bit !== 0 && bit !== 1))) throw Error(`${name} must be a rectangular binary integer matrix.`);
    return value;
  }
  function rank(matrix) { const a = matrix.map(r => r.slice()); let pivot = 0; for (let col = 0; col < a[0].length && pivot < a.length; col++) { const found = a.findIndex((row, i) => i >= pivot && row[col]); if (found < 0) continue; [a[pivot], a[found]] = [a[found], a[pivot]]; for (let i = pivot + 1; i < a.length; i++) if (a[i][col]) for (let j = col; j < a[i].length; j++) a[i][j] ^= a[pivot][j]; pivot++; } return pivot; }
  function parity(a, b) { let p = 0; for (let i = 0; i < a.length; i++) p ^= a[i] & b[i]; return p; }
  function css(code) {
    if (code.kind !== "embedded_css") return;
    const hx = matrix(code.hx, "hx"), hz = matrix(code.hz, "hz"), n = hx[0].length;
    if (hz[0].length !== n) throw Error("hx and hz must have the same number of columns.");
    if ([...hx, ...hz].some(row => row.every(bit => bit === 0))) throw Error("Code-capacity sampling rejects identity-only check rows.");
    if (hx.some(x => hz.some(z => parity(x, z)))) throw Error("hx and hz do not commute over GF(2).");
    if ((code.lx == null) !== (code.lz == null)) throw Error("Supply both lx and lz, or neither.");
    if (code.lx) { const lx = matrix(code.lx, "lx"), lz = matrix(code.lz, "lz"), k = n - rank(hx) - rank(hz);
      if (lx.length !== k || lz.length !== k || lx[0].length !== n || lz[0].length !== n) throw Error("Logical matrices must have shape (k,n).");
      if (lx.some(x => hz.some(z => parity(x, z))) || lz.some(z => hx.some(x => parity(x, z)))) throw Error("Logical rows do not commute with the opposite checks.");
      if (lx.some((x, i) => lz.some((z, j) => parity(x, z) !== Number(i === j)))) throw Error("Logical X/Z rows must have identity pairing.");
    }
  }
  const stopFields=['stop_failures','stop_type_i','stop_type_ii'];
  function sampling(spec,index){const base=spec.sampling,point=base.per_point?.[index]||base;return{shots:point.shots??null,...Object.fromEntries(stopFields.map(k=>[k,point[k]??null])),stop_mode:base.stop_mode||'any'};}
  function stopReason(limits,counts){const reached=stopFields.filter(k=>limits[k]!=null&&counts[k]>=limits[k]),enabled=stopFields.filter(k=>limits[k]!=null);if(limits.stop_mode==='all')return enabled.every(k=>reached.includes(k))&&(limits.shots==null||counts.shots>=limits.shots)?'all_targets':null;return stopFields.find(k=>reached.includes(k))||(limits.shots!=null&&counts.shots>=limits.shots?'shots_cap':null);}
  function sweepStim(text,source,p,contract){
    const noisy=new Set(contract.stim_noise_sweep?.noisy_gate_names||['CORRELATED_ERROR','DEPOLARIZE1','DEPOLARIZE2','E','ELSE_CORRELATED_ERROR','HERALDED_ERASE','HERALDED_PAULI_CHANNEL_1','II_ERROR','I_ERROR','M','MPP','MR','MRX','MRY','MRZ','MX','MXX','MY','MYY','MZ','MZZ','PAULI_CHANNEL_1','PAULI_CHANNEL_2','X_ERROR','Y_ERROR','Z_ERROR']);let replacements=0;
    const result=text.split('\n').map(line=>line.replace(/^(\s*)([A-Z][A-Z0-9_]*)(\[[^\]]*\])?(\s*)\(([^)]*)\)/,(match,prefix,name,tag,space,args)=>{
      if(!noisy.has(name))return match;const values=args.split(',').map(v=>v.trim());let changed=false;
      const next=values.map(v=>{const n=Number(v);if(v!==''&&known(n)&&Math.abs(n-source)<=1e-15){replacements++;changed=true;return String(p);}return v;});
      if(changed&&/CHANNEL/.test(name)&&next.reduce((sum,v)=>sum+Number(v),0)>1+1e-14)throw Error('Swept Pauli channel probabilities exceed one.');
      return changed?`${prefix}${name}${tag||''}${space}(${next.join(', ')})`:match;
    })).join('\n');
    if(!replacements)throw Error('The source probability does not match a noisy Stim gate argument. Set the source noise probability to a value in this circuit.');return result;
  }
  function validate(spec, contract) {
    const errors = [], check = (condition, message) => { if (!condition) errors.push(message); };
    const keys = contract.field_sets.experiment;
    if (!spec || typeof spec !== "object" || keys.some(k => !(k in spec)) || Object.keys(spec).some(k => !keys.includes(k))) return ["Use the complete research-experiment-v1 contract; unknown or missing fields are rejected."];
    const closed = (value, fields, name, optional = []) => {
      check(value && typeof value === "object" && !Array.isArray(value) && fields.every(k => optional.includes(k) || k in value) && Object.keys(value).every(k => fields.includes(k)), `${name}: unknown or missing fields in the shared contract.`);
    };
    const d = spec.decoder, circuit = spec.problem.kind === "circuit";
    closed(spec.sampling, [...new Set([...contract.field_sets.sampling, ...stopFields,"stop_mode","per_point"])], "sampling", [...stopFields,"stop_mode","per_point"]);
    closed(spec.budgets, contract.field_sets.budgets, "budgets");
    closed(spec.provenance, contract.field_sets.provenance, "provenance");
    closed(spec.problem, contract.field_sets[circuit ? "circuit_problem" : "code_problem"], "problem");
    closed(spec.channel, spec.channel.kind === "embedded_circuit" ? ["kind","noise_sweep"] : contract.field_sets[spec.channel.kind === "explicit" ? "explicit_channel" : "channel"], "channel", ["noise_sweep"]);
    const portable = d.implementation === "shared_policy" || d.implementation === "prior_tilt";
    const routeFields = ["shared_policy", "prior_tilt", "mbp4"];
    const decoderFields = [...new Set([...contract.field_sets[circuit ? "circuit_decoder" : "decoder"], ...routeFields, ...(!circuit && d.variant === "qbpgd" ? ["qbpgd"] : [])])];
    closed(d, decoderFields, "decoder", routeFields);
    if (errors.length) return errors;
    for (const field of ["stop_failures", "stop_type_i", "stop_type_ii"]) if (spec.sampling[field] != null) check(Number.isSafeInteger(spec.sampling[field]) && spec.sampling[field] > 0, `${field} must be a positive integer or empty.`);

    check(spec.schema === contract.schema, "Unsupported experiment schema."); check(typeof spec.id === "string" && spec.id.length > 0, "Supply an experiment label.");
    check(d.schedule === "flooding", "This execution backend supports flooding only; other schedules require a registered study route.");
    check(["binary_css", "bp4", "circuit_dem_bp"].includes(d.family), "Unsupported decoder family.");
    check(Array.isArray(spec.rate_points) && spec.rate_points.length > 0, "Supply at least one rate point.");
    check(contract.profiles[d.family]?.includes(d.numerical_profile), "The numerical profile does not belong to this decoder family.");
    check(["canonical_adaptation", "development_fixture"].includes(spec.provenance.relation), "A custom experiment cannot inherit a source-faithful result claim.");
    check(spec.provenance.source_spec_id === null || typeof spec.provenance.source_spec_id === "string", "source_spec_id must be a string or null.");
    check(spec.provenance.notes === null || typeof spec.provenance.notes === "string", "provenance.notes must be a string or null.");
    for (const k of ['seed','shot_start'])check(Number.isSafeInteger(spec.sampling[k])&&spec.sampling[k]>=0,`${k} must be a nonnegative integer.`);
    check(spec.sampling.stop_mode==null||['any','all'].includes(spec.sampling.stop_mode),'Stopping mode must be any or all.');
    if(spec.sampling.per_point!=null)check(Array.isArray(spec.sampling.per_point)&&spec.sampling.per_point.length===spec.rate_points.length,'Supply one budget object for each rate point.');
    if(spec.sampling.shots!=null)check(Number.isSafeInteger(spec.sampling.shots)&&spec.sampling.shots>0,'Shots must be a positive integer or empty.');
    for(let i=0;i<spec.rate_points.length;i++){
      if(spec.sampling.per_point){closed(spec.sampling.per_point[i],['shots',...stopFields],`Budgets for rate ${i+1}`);}
      const limits=sampling(spec,i),values=['shots',...stopFields].map(k=>limits[k]);
      check(values.some(v=>v!=null),`Rate point ${i+1}: at least one shot limit or failure target is required.`);
      check(values.every(v=>v==null||Number.isSafeInteger(v)&&v>0),`Rate point ${i+1}: limits must be positive integers or empty.`);
    }
    if(spec.budgets.max_shots!=null){check(Number.isSafeInteger(spec.budgets.max_shots)&&spec.budgets.max_shots>0,'Legacy total budget must be positive or null.');const targets=spec.rate_points.map((_,i)=>sampling(spec,i).shots);if(targets.every(v=>v!=null))check(spec.budgets.max_shots>=targets.reduce((a,b)=>a+b,0)+(circuit?spec.rate_points.length*spec.sampling.shot_start:0),'Legacy total budget is smaller than the per-point shot targets.');}
    check(Number.isSafeInteger(spec.budgets.max_iterations) && spec.budgets.max_iterations >= (circuit ? 0 : 1), "Supply an integer iteration cap.");
    if(portable){
      check(d.family === (circuit ? "circuit_dem_bp" : "binary_css"),"This policy requires binary CSS or a circuit detector error model.");
      if(!circuit)check(d.variant === "plain" && d.policy === null && d.stop_on_convergence === true,"The selected policy owns the binary check and stopping rules.");
      if(d.implementation === "prior_tilt"){
        const p=d.prior_tilt;
        closed(p,["initial","round_len","rounds","ends","phases"],"PriorTilt parameters",["ends","phases"]);
        check(!("shared_policy" in d),"Supply one canonical policy route.");
        check(p && Number.isSafeInteger(p.initial) && Number.isSafeInteger(p.round_len) && Number.isSafeInteger(p.rounds)
          && p.round_len>0 && p.initial>=p.round_len && p.rounds>=0 && p.initial+p.rounds*p.round_len<=spec.budgets.max_iterations,
          "PriorTilt requires a total sweep cap covering initial + rounds × round length.");
      }else{
        const p=d.shared_policy;
        check(!("prior_tilt" in d),"Supply one canonical policy route.");
        check(p?.version==="binary-policy-v1"&&["single",...(contract.shared_policy_controllers||[])].includes(p.controller),"Unknown canonical binary policy or controller.");
        if(p?.controller==="single")check(p.max_iterations===spec.budgets.max_iterations,"The shared policy iteration cap must match the total budget.");
        if(p?.controller==="guided_decimation")check(p.options?.round_limit*p.options?.sweeps_per_round<=spec.budgets.max_iterations,"BPGD rounds × sweeps exceed the total iteration budget.");
        if(p?.schedule==="layered")check(Array.isArray(p.partitions)&&p.partitions.length>0,"Layered scheduling requires check partitions.");
        if(p?.memory?.bindings?.some((b,i)=>b.kind==="pdprime_delta_mix"&&i!==0))errors.push("PD-prime delta mixing requires a fixed prior and the first field position.");
        if(p?.memory&&["residual","group_shuffled"].includes(p.schedule))errors.push("The selected schedule requires unmodified memory.");
      }
    }else if(d.implementation==="mbp4"){
      closed(d.mbp4,["alpha","schedule"],"MBP4 parameters");
      check(!circuit&&d.family==="bp4"&&d.variant==="plain"&&d.rule==="sum_product"&&d.policy===null&&d.stop_on_convergence===true&&
        known(d.mbp4?.alpha)&&d.mbp4.alpha>0&&["qbp_flooding","qbp_variable_serial"].includes(d.mbp4.schedule),
        "MBP4 requires a fixed positive α and a compatible Pauli schedule.");
      check(!("shared_policy" in d)&&!("prior_tilt" in d),"Supply one canonical policy route.");
    }else{
      check(!routeFields.some(k=>k in d),"The implementation must match the supplied policy route.");
      if(d.implementation==="qbp_variable_serial")check(!circuit&&d.family==="bp4"&&d.variant==="plain"&&d.rule==="sum_product"&&d.policy===null&&d.stop_on_convergence===true,
        "Variable-serial Q-BP uses the plain sum-product kernel and first-valid stopping.");
    }

    if (circuit) {
      closed(spec.problem.circuit, contract.field_sets[spec.problem.circuit?.kind === "registered" ? "registered_input" : "inline_stim"], "circuit");
      closed(spec.problem.dem, ["decompose_errors"], "dem");
      const sweep=spec.channel.noise_sweep;
      if(sweep){closed(sweep,['source_probability'],'Circuit noise sweep');check(known(sweep.source_probability)&&sweep.source_probability>0&&sweep.source_probability<1,'Source circuit noise must lie in [0,1].');}
      else check(spec.rate_points.length===1,'A circuit sweep needs its declared source noise probability.');
      for(const p of spec.rate_points){closed(p,sweep?['label','physical_p']:contract.field_sets.circuit_rate_point,'circuit rate point');check(typeof p.label==='string'&&p.label.length>0,'Circuit settings need a label.');if(sweep)check(known(p.physical_p)&&p.physical_p>=0&&p.physical_p<=1,'Circuit noise rates must lie in [0,1].');}
      if(sweep&&spec.problem.circuit?.kind==='inline_stim')for(const point of spec.rate_points)try{sweepStim(spec.problem.circuit.text,sweep.source_probability,point.physical_p,contract);}catch(e){errors.push(e.message);}
      check(d.family === "circuit_dem_bp" && (d.implementation === "canonical_sinter" || portable) && contract.rules_by_family.circuit_dem_bp.includes(d.rule) && d.numerical_profile === contract.circuit_rule_profiles[d.rule], "The detector-kernel rule and profile do not agree.");
      check(!("policy" in d) && !["damping", "resolution", "variant"].some(k => k in d), "Circuit damping, resolution overlays, and interventions are unsupported.");
      check(spec.channel.kind === "embedded_circuit" && spec.problem.dem?.decompose_errors === false, "Circuit noise comes from Stim text and requires decompose_errors=false.");
      check(spec.problem.circuit?.kind === "registered" || (spec.problem.circuit?.kind === "inline_stim" && typeof spec.problem.circuit.text === "string" && spec.problem.circuit.text.trim().length > 0), "Supply Stim text or a registered circuit.");
      if(spec.budgets.max_shots!=null&&spec.sampling.shots!=null)check(spec.sampling.shot_start+spec.sampling.shots<=spec.budgets.max_shots,"Circuit skipped prefix consumes the legacy total shot budget.");
      check(["zero", "one"].includes(d.tie_break), "Unsupported circuit tie policy.");
      check(Number.isSafeInteger(d.max_iterations) && d.max_iterations >= 0 && d.max_iterations <= spec.budgets.max_iterations, "Circuit decoder iteration cap exceeds the budget.");
    } else {
      const input = spec.problem.code;
      closed(input, contract.field_sets[input?.kind === "registered" ? "registered_input" : "embedded_css"], "code", ["lx", "lz"]);
      check(contract.code_kinds.includes(input?.kind), "Unsupported code input format.");
      check(spec.problem.kind === (d.family === "bp4" ? "pauli_code_capacity" : "css_code_capacity"), "Decoder family and problem regime disagree.");
      check(["depolarizing", "x_only", "explicit"].includes(spec.channel.kind), "Unsupported code-capacity noise model.");
      check(contract.rules.includes(d.rule), "Unsupported update rule.");
      check(d.implementation === "compiled" || ["mbp4","qbp_variable_serial"].includes(d.implementation) || portable, "Unknown canonical implementation.");
      if (d.family === "binary_css") check(d.variant === "plain" && d.stop_on_convergence === true, "Binary compiled BP uses first-valid stopping and plain BP only.");
      if (d.family === "binary_css" && d.rule === "min_sum") check(d.policy !== null, "Binary min-sum requires its explicit v2 numerical policy overlay.");
      if (d.family === "bp4") check(["plain", "qbpgd"].includes(d.variant) && typeof d.stop_on_convergence === "boolean", "Unsupported BP4 procedure or stopping rule.");
      if (!d.numerical_profile?.endsWith("-v1") && !d.numerical_profile?.endsWith("-v2")) errors.push("Unknown numerical profile.");
      if (d.numerical_profile?.endsWith("-v1")) check(d.rule === "sum_product" && d.policy === null && d.variant === "plain", "Frozen v1 requires plain sum-product and no numerical overlay.");
      try { css(spec.problem.code); } catch (error) { errors.push(error.message); }
      for (const p of spec.rate_points) { closed(p, contract.field_sets[spec.channel.kind === "explicit" ? "explicit_rate_point" : "rate_point"], "rate point"); if (spec.channel.kind !== "explicit") check(known(p.physical_p) && p.physical_p >= 0 && p.physical_p <= 1, "Physical p must lie in [0,1]."); check(known(p.decoder_p0) && p.decoder_p0 > 0 && p.decoder_p0 < 1, "Decoder p₀ must lie strictly between 0 and 1."); }
      if (spec.channel.kind === "explicit") {
        const probabilities = spec.channel.probabilities, table = Array.isArray(probabilities?.[0]) ? probabilities : [probabilities];
        check(table.every(row => Array.isArray(row) && row.length === 4 && row.every(p => known(p) && p >= 0 && p <= 1) && Math.abs(row.reduce((a, b) => a + b, 0) - 1) <= 8 * Number.EPSILON), "Explicit Pauli probabilities must be normalized I,X,Y,Z rows.");
        if (input.kind === "embedded_css") check(table.length === 1 || table.length === input.hx[0].length, "Per-qubit probability rows must match n.");
      }
      if (d.policy) {
        const p = d.policy, r = p.resolution;
        closed(p, contract.field_sets.policy, "policy"); closed(r, contract.field_sets.resolution, "resolution");
        check(d.numerical_profile.endsWith("-v2") && p.check_rule === d.rule && p.version === contract.ui_fields.policy.version, "Policy overlay must match the v2 profile and check rule.");
        check(r && r.version === contract.ui_fields.policy.resolution_version && contract.resolution.formats.includes(r.format) && contract.resolution.scopes.includes(r.scope) && contract.resolution.coefficients.includes(r.coefficients), "Unknown resolution policy.");
        if (r?.format.startsWith("int")) check(Number.isSafeInteger(r.scale) && r.scale > 0 && r.scale <= 2147483647, "Fixed-point scale must be a positive int32-range integer."); else check(r?.scale === null, "Floating formats use scale=null.");
        check(known(p.damping) && p.damping >= 0 && p.damping < 1 && known(p.alpha) && p.alpha > 0 && known(p.beta) && p.beta >= 0, "Invalid damping, scale, or offset coefficient.");
        if (d.rule === "sum_product") check(p.alpha === 1 && p.beta === 0, "SPA does not accept min-sum scale or offset.");
        if (d.family === "binary_css") check(p.hard_decision === "min_llr", "A Pauli hard-decision policy cannot modify a binary decoder.");
        check(["min_llr", "strict_pauli"].includes(p.hard_decision) && typeof p.zero_syndrome_shortcut === "boolean", "Unsupported hard-decision or shortcut policy.");
      }
      if (d.variant === "qbpgd") { closed(d.qbpgd, contract.field_sets.qbpgd, "qbpgd"); check(d.family === "bp4" && ["sum_product","min_sum"].includes(d.rule) && d.stop_on_convergence === true && d.numerical_profile === "quaternary-bp4-f64-v2" && Number.isSafeInteger(d.qbpgd?.round_limit) && d.qbpgd.round_limit > 0 && Number.isSafeInteger(d.qbpgd?.iterations_per_round) && d.qbpgd.iterations_per_round > 0 && d.qbpgd.round_limit * d.qbpgd.iterations_per_round <= spec.budgets.max_iterations && known(d.qbpgd.epsilon) && d.qbpgd.epsilon > 0 && d.qbpgd.epsilon < 1, "Q-BPGD needs the compatible quaternary v2 policy, first-valid stopping, and rounds × sweeps within the total iteration cap."); }
    }
    return errors;
  }

window.ResearchValidation={validate,sampling,stopReason,sweepStim,stopFields};
})();
