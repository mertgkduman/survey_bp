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
  function validate(spec, contract) {
    const errors = [], check = (condition, message) => { if (!condition) errors.push(message); };
    const keys = contract.field_sets.experiment;
    if (!spec || typeof spec !== "object" || keys.some(k => !(k in spec)) || Object.keys(spec).some(k => !keys.includes(k))) return ["Use the complete research-experiment-v1 contract; unknown or missing fields are rejected."];
    const closed = (value, fields, name, optional = []) => {
      check(value && typeof value === "object" && !Array.isArray(value) && fields.every(k => optional.includes(k) || k in value) && Object.keys(value).every(k => fields.includes(k)), `${name}: unknown or missing fields in the shared contract.`);
    };
    const d = spec.decoder, circuit = spec.problem.kind === "circuit";
    closed(spec.sampling, [...new Set([...contract.field_sets.sampling, "stop_failures", "stop_type_i", "stop_type_ii"])], "sampling", ["stop_failures", "stop_type_i", "stop_type_ii"]);
    closed(spec.budgets, contract.field_sets.budgets, "budgets");
    closed(spec.provenance, contract.field_sets.provenance, "provenance");
    closed(spec.problem, contract.field_sets[circuit ? "circuit_problem" : "code_problem"], "problem");
    closed(spec.channel, contract.field_sets[spec.channel.kind === "explicit" ? "explicit_channel" : "channel"], "channel");
    const decoderFields = [...contract.field_sets[circuit ? "circuit_decoder" : "decoder"], ...(!circuit && d.variant === "qbpgd" ? ["qbpgd"] : [])];
    closed(d, decoderFields, "decoder");
    if (errors.length) return errors;
    for (const field of ["stop_failures", "stop_type_i", "stop_type_ii"]) if (spec.sampling[field] != null) check(Number.isSafeInteger(spec.sampling[field]) && spec.sampling[field] > 0, `${field} must be a positive integer or empty.`);
    if (circuit) check(spec.sampling.stop_type_i == null && spec.sampling.stop_type_ii == null, "Circuit experiments use observable failures; Type I/II targets are unsupported.");
    check(spec.schema === contract.schema, "Unsupported experiment schema."); check(typeof spec.id === "string" && spec.id.length > 0, "Supply an experiment label.");
    check(d.schedule === "flooding", "This execution backend supports flooding only; other schedules require a registered study route.");
    check(["binary_css", "bp4", "circuit_dem_bp"].includes(d.family), "Unsupported decoder family.");
    check(Array.isArray(spec.rate_points) && spec.rate_points.length > 0, "Supply at least one rate point.");
    check(contract.profiles[d.family]?.includes(d.numerical_profile), "The numerical profile does not belong to this decoder family.");
    check(["canonical_adaptation", "development_fixture"].includes(spec.provenance.relation), "A custom experiment cannot inherit a source-faithful result claim.");
    check(spec.provenance.source_spec_id === null || typeof spec.provenance.source_spec_id === "string", "source_spec_id must be a string or null.");
    check(spec.provenance.notes === null || typeof spec.provenance.notes === "string", "provenance.notes must be a string or null.");
    for (const k of ["shots", "seed", "shot_start"]) check(Number.isSafeInteger(spec.sampling[k]) && spec.sampling[k] >= (k === "shots" ? 1 : 0), `${k} must be an integer in its supported range.`);
    check(Number.isSafeInteger(spec.budgets.max_shots) && spec.budgets.max_shots >= spec.rate_points.length * spec.sampling.shots, "The total shot budget must cover all rate points × shots.");
    check(Number.isSafeInteger(spec.budgets.max_iterations) && spec.budgets.max_iterations >= (circuit ? 0 : 1), "Supply an integer iteration cap.");
    if (circuit) {
      closed(spec.problem.circuit, contract.field_sets[spec.problem.circuit?.kind === "registered" ? "registered_input" : "inline_stim"], "circuit");
      closed(spec.problem.dem, ["decompose_errors"], "dem");
      check(spec.rate_points.length === 1, "One Stim circuit has one embedded noise setting; use separate circuits for a sweep.");
      for (const p of spec.rate_points) closed(p, contract.field_sets.circuit_rate_point, "circuit rate point");
      check(d.family === "circuit_dem_bp" && d.implementation === "canonical_sinter" && contract.rules_by_family.circuit_dem_bp.includes(d.rule) && d.numerical_profile === contract.circuit_rule_profiles[d.rule], "Circuit execution supports only the pinned plain float64 v1 Sinter adapter.");
      check(!("policy" in d) && !["damping", "resolution", "variant"].some(k => k in d), "Circuit damping, resolution overlays, and interventions are unsupported.");
      check(spec.channel.kind === "embedded_circuit" && spec.problem.dem?.decompose_errors === false, "Circuit noise comes from Stim text and requires decompose_errors=false.");
      check(spec.problem.circuit?.kind === "registered" || (spec.problem.circuit?.kind === "inline_stim" && typeof spec.problem.circuit.text === "string" && spec.problem.circuit.text.trim().length > 0), "Supply Stim text or a registered circuit.");
      check(spec.sampling.shot_start + spec.sampling.shots <= spec.budgets.max_shots, "Circuit skipped prefix consumes the total shot budget.");
      check(["zero", "one"].includes(d.tie_break), "Unsupported circuit tie policy.");
      check(Number.isSafeInteger(d.max_iterations) && d.max_iterations >= 0 && d.max_iterations <= spec.budgets.max_iterations, "Circuit decoder iteration cap exceeds the budget.");
    } else {
      const input = spec.problem.code;
      closed(input, contract.field_sets[input?.kind === "registered" ? "registered_input" : "embedded_css"], "code", ["lx", "lz"]);
      check(contract.code_kinds.includes(input?.kind), "Unsupported code input format.");
      check(spec.problem.kind === (d.family === "bp4" ? "pauli_code_capacity" : "css_code_capacity"), "Decoder family and problem regime disagree.");
      check(["depolarizing", "x_only", "explicit"].includes(spec.channel.kind), "Unsupported code-capacity noise model.");
      check(contract.rules.includes(d.rule), "Unsupported update rule.");
      check(d.implementation === "compiled", "This custom experiment route uses the compiled canonical implementation.");
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
      if (d.variant === "qbpgd") { closed(d.qbpgd, contract.field_sets.qbpgd, "qbpgd"); check(d.family === "bp4" && d.rule === "sum_product" && d.stop_on_convergence === true && d.numerical_profile === "quaternary-bp4-f64-v2" && d.policy === null && Number.isSafeInteger(d.qbpgd?.round_limit) && d.qbpgd.round_limit > 0 && Number.isSafeInteger(d.qbpgd?.iterations_per_round) && d.qbpgd.iterations_per_round > 0 && d.qbpgd.round_limit * d.qbpgd.iterations_per_round <= spec.budgets.max_iterations && known(d.qbpgd.epsilon) && d.qbpgd.epsilon > 0 && d.qbpgd.epsilon < 1, "Q-BPGD needs sum-product v2, first-valid stopping, no resolution overlay, and rounds × sweeps within the total iteration cap."); }
    }
    return errors;
  }

window.ResearchValidation={validate};
})();
