#!/usr/bin/env python3
"""Build and gate the finite Phase 4 factorial; this command never samples."""
from __future__ import annotations
import argparse, json, re, subprocess, sys
from collections import Counter, defaultdict
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from time import perf_counter
from typing import Any, Callable, Mapping
from bp_registry.phase4_analysis import CELLS, wilson_interval

ROOT=Path(__file__).resolve().parents[1]
TARGET={"affine_prior":"prior","v2c_damping":"v2c","pdbp_field_mix":"belief","pdprime_delta_mix":"belief","posterior_momentum":"posterior"}
def _j(x): return json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=True)
def _d(x): return sha256(_j(x).encode()).hexdigest()
def _read(p):
    x=json.loads(Path(p).read_text())
    if not isinstance(x,dict): raise ValueError("expected JSON object")
    return x
def _sha(p): return sha256(Path(p).read_bytes()).hexdigest()
def _active():
    p=str(Path(__file__).parent)
    if p not in sys.path: sys.path.insert(0,p)
    import run_phase4_active_benchmark as active
    return active

def _validate(design,caps,s):
    if s.get("status")!="frozen_pre_sampling" or s.get("calibration_outcomes_inspected") is not False: raise ValueError("supplement is not outcome-independent")
    if s.get("supplement_digest")!=_d({k:v for k,v in s.items() if k!="supplement_digest"}): raise ValueError("supplement digest does not verify")
    binds=s.get("input_digests",{})
    if binds.get("design_canonical_sha256")!=_d(design) or binds.get("caps_canonical_sha256")!=_d(caps): raise ValueError("supplement input digest mismatch")
    if caps.get("status")!="frozen_pre_calibration": raise ValueError("caps are not frozen active-V4")

def _ordinary(arm,s):
    frozen=list(arm.get("memory_bindings",[])); e=s.get("ordinary_memory_arms",{}).get(arm["id"])
    if e is None:return frozen,frozen,[],True
    if e.get("frozen_binding_array")!=frozen: raise ValueError("frozen binding array changed")
    order=e.get("effective_execution_order"); co=e.get("coefficients"); aliases=e.get("frozen_aliases",{})
    if not isinstance(order,list) or not isinstance(co,list) or sorted(aliases.get(x,x) for x in frozen)!=sorted(order): raise ValueError("invalid ordinary binding resolution")
    return frozen,order,[dict(x) for x in co],e.get("execution_ready") is True

def _trace_budgets(caps, arms):
    """Split the frozen per-code aggregate trace quota across selected arms."""
    fixture=caps["fixture_trace"]; out={}
    for code, detail in caps["codes"].items():
        factorial_shots=int(fixture["factorial_shots_per_arm_rate_code_by_code"][code])
        fixture_shots=int(fixture["fixture_shots_per_code"][code])
        trace_caps=dict(detail["trace_caps"]); selected=len(arms)
        if factorial_shots <= 0 or fixture_shots <= 0 or selected > int(trace_caps["max_shots"]):
            raise ValueError("frozen factorial trace shot budget is exceeded")
        # The trace caps are per code, so each selected arm receives a fixed
        # floor allocation.  It is one existing factorial shot, not an extra
        # fixture shot; the separate fixture allocation remains untouched.
        out[code]={"aggregate":trace_caps,"selected_trace_cells":selected,
                   "factorial_shots_per_arm_rate_code":factorial_shots,
                   "separate_fixture_shots_per_code":fixture_shots,
                   "per_trace":{"max_records":int(trace_caps["max_records"])//selected,
                                "max_bytes":int(trace_caps["max_bytes"])//selected}}
        if not all(value > 0 for value in out[code]["per_trace"].values()):
            raise ValueError("frozen aggregate trace cap cannot admit every selected arm")
    return out

def build_factorial_plan(*,design,caps,supplement):
    _validate(design,caps,supplement); arms=design["factorial_arms"]; grid=design["noise_grid"]; fact=caps["factorial"]
    if [a["id"] for a in arms]!=fact["arms"]: raise ValueError("factorial cap arms drifted")
    cells=[]
    for code,identity in sorted(design["codes"].items()):
      for region in grid:
       rate=float(region["error_rates"][code]); ns=f"{identity['sample_namespace']}-factorial-v1-p{rate:.3f}".replace(".","")
       for shot in range(int(fact["shots_per_arm_rate_code_by_code"][code])):
        physical=_d({"namespace":ns,"shot_id":shot})
        for arm in arms:
         frozen,order,co,ready=_ordinary(arm,supplement); aid=arm["id"]
         cells.append({"cell_id":_d({"code":code,"region":region["region"],"shot":shot,"arm":aid,"supplement":supplement["supplement_digest"]})[:24],"code_id":code,"noise_region":region["region"],"error_rate":rate,"shot_id":shot,"arm_id":aid,"arm_kind":arm["kind"],"relay_control":arm.get("control"),"factorial_namespace":ns,"physical_sample_identity":physical,"original_binding_array":frozen,"execution_order":order,"coefficients":co,"execution_ready":ready,"work_cap":dict(caps["codes"][code]["per_shot_work_cap"]),"runtime_boundary_seconds":int(fact["runtime_boundary_seconds"]),"fidelity":{"status":"controlled_css_pilot_adaptation","assessment":"not_assessed"}})
    trace_contract={**supplement["trace_contract"],"budgets_by_code":_trace_budgets(caps,arms),"preselected_clean_profile_rule":"visible_bp_failures/shot-0 for every factorial arm; deterministic before outcomes","preselected_shots_per_code":len(arms),"fixture_shot_interpretation":"The frozen seven fixture shots per code are a separate fixture allocation. Each selected trace is the already-admitted factorial shot 0 for its arm, so fourteen trace cells per code consume no extra fixture shots and remain within trace_caps.max_shots=32."}
    out={"schema_version":1,"status":"prepared_no_sampling","assessment":{"status":"not_assessed","scope":"CSS_pilot_adaptation"},"input_digests":{"design_canonical_sha256":_d(design),"caps_canonical_sha256":_d(caps),"caps_digest":caps["caps_digest"],"supplement_digest":supplement["supplement_digest"]},"cells":cells,"cell_count":len(cells),"outcome_cells":list(CELLS),"factorial_category_wall_seconds_max":float(caps["allocation"]["categories"]["fixture_trace"]["wall_seconds_max"]),"blocked_execution_arms":sorted({c["arm_id"] for c in cells if not c["execution_ready"]}),"execution_order_note":supplement["execution_order_resolution"],"trace_contract":trace_contract}
    out["factorial_digest"]=_d(out); return out

def _binding(cell,index,item,seed):
    kind=item["kind"]; params={k:float(v) for k,v in item["parameters"].items() if k in {"alpha","gamma"}}; bid=f"factorial-{cell['arm_id']}-{kind}-{index}".replace("_","-")
    out={"binding_id":bid,"kind":kind,"target":TARGET[kind],"parameters":params,"order":index,"history_owner":f"memory:{bid}","state_lifetime":"attempt","advance_boundary":"source_iteration","refresh_boundary":"attempt_start","source_status":"canonical_adaptation","retain_history":False}
    if item["parameters"].get("assignment")=="per_source_iteration_digest_bound": out["assignment"]={"mode":"uniform","low":0.0,"high":1.0,"root_seed_identity":_d({"seed":seed,"binding":bid}),"refresh_boundary":"source_iteration","rng_algorithm":"numpy.PCG64"}
    return out

def build_public_manifest(*,repository_root,cell,plan):
    active=_active(); base=_read(Path(repository_root)/active.CODE_MANIFESTS[cell["code_id"]]); ordinary=bool(cell["coefficients"])
    relay_arm="baseline" if ordinary or cell["arm_id"] in {"baseline","relay-one-leg"} else "canonical_relay_31"
    seed=_d({"plan":plan["factorial_digest"],"code":cell["code_id"],"rate":cell["error_rate"],"arm":cell["arm_id"]})
    value=active.build_active_manifest(base,arm=relay_arm,preset="canonical_default",error_rate=float(cell["error_rate"]),first_leg_gamma=0.0,later_center=0.0,later_width=0.0,seed_identity=seed,work_profile="b1_three_leg" if cell["code_id"]=="b1-ghp-882" else "full31")
    value["run_id"]="phase4-factorial-"+_d({"cell":cell["cell_id"],"plan":plan["factorial_digest"]})[:24]; value["randomness"]["physical_sample_identity"]=cell["factorial_namespace"]; value["randomness"]["decoder_seed_identity"]=seed; value["budgets"]["max_shots"]=7
    for scope in ("shot","search","attempt"): value["budgets"][scope]["work_limits"]=dict(cell["work_cap"])
    if ordinary: value["memory"]={"bindings":[_binding(cell,i,x,seed) for i,x in enumerate(cell["coefficients"])]}
    elif cell["arm_id"]=="baseline": value["memory"]={"bindings":[_binding({**cell,"arm_id":"baseline"},0,{"kind":"affine_prior","parameters":{"alpha":0.0}},seed)]}
    relay=value["relay"]
    if cell["arm_id"]=="relay-no-transfer": relay["transfer"]="disabled"
    if cell["arm_id"]=="relay-uniform-later-memory": relay.pop("memory_tuning",None); relay["later_leg_memory"]="uniform"
    if cell["arm_id"]=="relay-disordered-later-memory": relay["later_leg_memory"]="disordered"
    trace_caps=plan["trace_contract"]["budgets_by_code"][cell["code_id"]]["per_trace"]
    selected_trace=(cell["noise_region"]=="visible_bp_failures" and cell["shot_id"]==0)
    value["trace_plan"]={"level":"full" if selected_trace else "off",
                         "relative_dir":f"factorial-traces/{cell['code_id']}/{cell['noise_region']}/{cell['arm_id']}",
                         "max_records":int(trace_caps["max_records"]) if selected_trace else 0,
                         "max_bytes":int(trace_caps["max_bytes"]) if selected_trace else 0,
                         "label":"prespecified_campaign"}
    value["evidence"]["discrepancies"].append(
        "Trace selection is pre-outcome diagnostic evidence; disagreement/tail replays are not population performance estimates.")
    value["evidence"]["procedure"]+=f" Phase 4 factorial arm={cell['arm_id']}; digest={plan['factorial_digest']}."; value["evidence"]["discrepancies"].append("Finite CSS pilot adaptation; not a circuit reproduction or universal ranking.")
    return value

def preflight_manifest(manifest):
    from bp_registry.manifests import parse_manifest
    parse_manifest(dict(manifest))
def materialize_public_manifests(*,repository_root,plan,code_id):
    out={}; by_region=defaultdict(set)
    for cell in plan["cells"]:
      if cell["code_id"]!=code_id or cell["shot_id"]!=0: continue
      manifest=build_public_manifest(repository_root=repository_root,cell=cell,plan=plan); preflight_manifest(manifest); out[f"{cell['noise_region']}/{cell['arm_id']}"]=manifest; by_region[cell["noise_region"]].add(manifest["randomness"]["physical_sample_identity"])
    if any(len(x)!=1 for x in by_region.values()): raise ValueError("public factorial samples are not matched")
    return out

def development_fixture_evaluation(plan):
    arms=("baseline","selected_source_procedure","selected_canonical_procedure")
    return {"schema_version":1,"status":"completed","development_fixture":True,"assessment":"not_assessed","caps_digest":plan["input_digests"]["caps_digest"],"plan_digest":"fixture","selected_settings_digest":"fixture","codes":{code:{a:{"status":"completed"} for a in arms} for code in sorted({x["code_id"] for x in plan["cells"]})}}

def _digest_text(value):
    return isinstance(value,str) and re.fullmatch(r"[0-9a-f]{64}",value) is not None

def _expected_evaluation_provenance(repository_root):
    """Fail closed unless calibration and frozen three-arm selection verify."""
    root=Path(repository_root); selection_path=root/"data/results/phase4-memory-relay/selected-settings.json"
    if not selection_path.exists(): raise ValueError("retained selected settings are absent for genuine factorial predecessor")
    import run_phase4_evaluation as evaluation
    caps, _calibration, selection=evaluation.verified_inputs(
        root=root, caps_path=root/"data/manifests/phase4-pilot-caps.json",
        calibration_path=root/"data/results/phase4-memory-relay/calibration/result.json",
        selection_path=selection_path, freeze_selection=False,
    )
    expected=evaluation.evaluation_plan(caps,selection)
    return {"plan_digest":evaluation._digest(expected),"selected_settings_digest":evaluation._digest(selection),"arms":("baseline","selected_source_procedure","selected_canonical_procedure")}

def assert_factorial_predecessor(*,evaluation_path,plan,allow_development_fixture=False,repository_root=ROOT):
    e=_read(evaluation_path); fixture=e.get("development_fixture") is True; arms=("baseline","selected_source_procedure","selected_canonical_procedure"); codes={x["code_id"] for x in plan["cells"]}
    if fixture and (not allow_development_fixture or e.get("assessment")!="not_assessed"): raise ValueError("development fixture cannot authorize production factorial sampling")
    if e.get("status")!="completed": raise ValueError("fresh evaluation is absent, incomplete, or inconclusive")
    if e.get("caps_digest")!=plan["input_digests"]["caps_digest"]:
        raise ValueError("fresh evaluation digest contract differs")
    if not fixture and (not _digest_text(e.get("plan_digest")) or not _digest_text(e.get("selected_settings_digest"))):
        raise ValueError("fresh evaluation digest contract differs")
    expected=None if fixture else _expected_evaluation_provenance(repository_root)
    if expected is not None and (e["plan_digest"]!=expected["plan_digest"] or e["selected_settings_digest"]!=expected["selected_settings_digest"]):
        raise ValueError("fresh evaluation provenance differs from the retained three-arm evaluation plan")
    if not isinstance(e.get("codes"),Mapping) or set(e["codes"])!=codes or any(e["codes"][c].get(a,{}).get("status")!="completed" for c in codes for a in arms): raise ValueError("fresh evaluation is not complete for its frozen three-arm cohort")
    return {"path":str(evaluation_path),"sha256":_sha(evaluation_path),"development_fixture":fixture,"assessment":"not_assessed","evaluation_plan_digest":e["plan_digest"],"selected_settings_digest":e["selected_settings_digest"]}

def _tails(values):
    if not values:return {"p50":None,"p95":None,"max":None}
    s=sorted(values); return {"p50":s[len(s)//2],"p95":s[min(len(s)-1,round(.95*(len(s)-1)))],"max":s[-1]}
def aggregate_terminals(rows,plan):
    groups=defaultdict(list)
    for r in rows: groups[(r["code_id"],r["noise_region"],r["arm_id"])].append(r)
    summary={}
    for key,rs in groups.items():
      complete=[r for r in rs if r.get("execution_status")=="completed"]; cells=Counter(r.get("diagnostic_cell") for r in complete)
      if set(cells)-set(CELLS): raise ValueError("completed factorial terminal has invalid diagnostic cell")
      failures=sum(not(r.get("selected") is True and r.get("diagnostic_cell")=="valid_correct") for r in complete); valid=[r for r in complete if r.get("selected") is True and r.get("diagnostic_cell") in {"valid_correct","valid_wrong_logical"}]; wrong=sum(r.get("diagnostic_cell")=="valid_wrong_logical" for r in valid)
      trace_statuses=Counter(str(r.get("trace",{}).get("status","missing")) for r in rs)
      summary["/".join(key)]={"planned":7,"attempted":len(rs),"completed":len(complete),"incomplete_or_unstarted":7-len(complete),"diagnostic_cells":{c:cells[c] for c in CELLS},"all_shot_failure":{"failures":failures,"denominator":len(complete),"estimate":failures/len(complete) if complete else None,"wilson_95":wilson_interval(failures,len(complete))},"selected_valid_syndrome_logical_error":{"failures":wrong,"denominator":len(valid),"wilson_95":wilson_interval(wrong,len(valid))},"execution_statuses":dict(Counter(r.get("execution_status") for r in rs)),"raw_work":[r.get("raw_work") for r in rs],"runtime_seconds":_tails([float(r["runtime_seconds"]) for r in rs if isinstance(r.get("runtime_seconds"),(int,float))]),"resource_maxrss_kib":{"tails":_tails([float(r.get("resource",{}).get("maxrss_kib")) for r in rs if isinstance(r.get("resource",{}).get("maxrss_kib"),(int,float))]),"missing":sum(not isinstance(r.get("resource",{}).get("maxrss_kib"),(int,float)) for r in rs)},"trace":{"statuses":dict(trace_statuses),"missing":trace_statuses["missing"]+trace_statuses["unavailable"]}}
    return {"by_cell":summary,"outcome_cells":list(CELLS)}

def trace_evidence(events, *, cell, plan):
    """Index the public trace event without converting absence into a result."""
    selected = cell["noise_region"] == "visible_bp_failures" and cell["shot_id"] == 0
    if not selected:
        return {"status":"not_selected_pre_outcome","selection_basis":"visible_bp_failures/shot-0"}
    events = [event for event in events if event.get("shot_id") == cell["shot_id"] and event.get("kind") == "trace_link"]
    if not events:
        return {"status":"unavailable","reason":"no_public_trace_link","selection_basis":"visible_bp_failures/shot-0"}
    event = events[-1]; data = event.get("data", {})
    if not isinstance(data, Mapping) or data.get("status") != "linked":
        return {"status":"unavailable","reason":data.get("reason","public_trace_unavailable") if isinstance(data, Mapping) else "invalid_trace_event","selection_basis":"visible_bp_failures/shot-0"}
    sidecar = event.get("sidecar")
    if not isinstance(sidecar, Mapping):
        return {"status":"unavailable","reason":"linked_trace_missing_sidecar","selection_basis":"visible_bp_failures/shot-0"}
    caps = plan["trace_contract"]["budgets_by_code"][cell["code_id"]]["per_trace"]
    records, bytes_written = sidecar.get("records"), sidecar.get("bytes")
    if type(records) is not int or type(bytes_written) is not int or records > caps["max_records"] or bytes_written > caps["max_bytes"]:
        raise ValueError("public trace sidecar exceeds or omits frozen trace caps")
    if not isinstance(sidecar.get("truncated"), bool) or type(sidecar.get("dropped_records")) is not int:
        raise ValueError("public trace sidecar omits truncation evidence")
    return {"status":"linked","trace_kind":data.get("trace_kind"),"sidecar":dict(sidecar),"selection_basis":"visible_bp_failures/shot-0"}

def _retained_trace_evidence(active, run_root, *, cell, plan):
    return trace_evidence(active._events(run_root), cell=cell, plan=plan) if (run_root / "events.jsonl").exists() else trace_evidence([], cell=cell, plan=plan)

def validate_trace_inventory(rows, plan):
    """Enforce the frozen per-code aggregate quota after every retained shot."""
    linked=defaultdict(list); selected=Counter()
    for row in rows:
        trace=row.get("trace", {})
        if trace.get("selection_basis") == "visible_bp_failures/shot-0":
            selected[row["code_id"]] += 1
        if trace.get("status") == "linked": linked[row["code_id"]].append(trace["sidecar"])
    for code, budget in plan["trace_contract"]["budgets_by_code"].items():
        aggregate=budget["aggregate"]
        if selected[code] > int(aggregate["max_shots"]):
            raise ValueError("retained selected traces exceed frozen per-code shot cap")
        if sum(int(item["records"]) for item in linked[code]) > int(aggregate["max_records"]) or sum(int(item["bytes"]) for item in linked[code]) > int(aggregate["max_bytes"]):
            raise ValueError("retained trace sidecars exceed frozen per-code aggregate cap")
    return True

def canonical_public_executor(*, repository_root: Path, output_root: Path, plan: Mapping[str, Any]) -> Callable[[Mapping[str, Any]], Mapping[str, Any]]:
    """Return the production executor: public preflight, one shot, then verify."""
    active=_active()
    spent=0.0
    def execute(cell):
      nonlocal spent
      boundary=float(cell["runtime_boundary_seconds"])
      category_remaining=float(plan["factorial_category_wall_seconds_max"])-spent
      cell_deadline_seconds=min(boundary,category_remaining)
      if cell_deadline_seconds <= 0:
        return {"cell_id":cell["cell_id"],"sample_namespace":cell["factorial_namespace"],"sample_identity":None,"execution_status":"incomplete_category_cap","terminal":False,"raw_work":None,"runtime_seconds":None,"resource":{"maxrss_kib":None},"category_remaining_seconds":max(0.0,category_remaining)}
      manifest=build_public_manifest(repository_root=repository_root,cell=cell,plan=plan)
      # A manifest's trace plan applies to its whole run.  Isolating a cell keeps
      # the prespecified shot-0 diagnostic trace from collecting the other six
      # shots in an arm/rate cohort.
      root=output_root/cell["code_id"]/cell["noise_region"]/cell["arm_id"]/f"shot-{cell['shot_id']}"; root.mkdir(parents=True,exist_ok=True)
      path=root/"manifest.json"; expected=json.dumps(manifest,indent=2,sort_keys=True)+"\n"
      if path.exists() and path.read_text()!=expected: raise ValueError("retained factorial manifest drifted")
      if not path.exists(): path.write_text(expected)
      artifact={"manifest_path":str(path),"manifest_sha256":_sha(path),"run_dir":str(root/"run"),"ledger_path":str(root/"run"/"events.jsonl")}
      began=None
      try:
        began=perf_counter()
        deadline=began+cell_deadline_seconds
        def invoke(*command):
          remaining=deadline-perf_counter()
          if remaining <= 0: raise subprocess.TimeoutExpired(command,cell_deadline_seconds)
          return active._command(repository_root,*command,timeout=remaining)
        preflight=invoke("preflight",str(path))
        observation=invoke("canonical-observation",str(path),"--shot",str(cell["shot_id"]))
        if observation.get("sample_namespace")!=cell["factorial_namespace"] or not isinstance(observation.get("sample_identity"),str): raise ValueError("public observation does not expose the declared factorial sample identity")
        run=invoke("canonical",str(path),"--output",str(root/"run"),"--shot",str(cell["shot_id"]))
        verify=invoke("verify-canonical-shot",str(path),str(root/"run"),"--shot",str(cell["shot_id"]))
        events=active._events(root/"run"); fact=active._attempt_from_events(events,cell["shot_id"]); trace=trace_evidence(events,cell=cell,plan=plan); terminal=fact["terminal"]
        if fact["sample_identity"] not in {None,observation["sample_identity"]}: raise ValueError("public ledger sample identity disagrees with public observation")
        elapsed=perf_counter()-began; spent += elapsed
        if fact["termination"] is None: return {"cell_id":cell["cell_id"],"sample_namespace":observation["sample_namespace"],"sample_identity":observation["sample_identity"],"execution_status":"incomplete_public_boundary","terminal":False,"raw_work":fact["work_vector"],"runtime_seconds":elapsed,"resource":{"maxrss_kib":None},"trace":trace,"artifact":artifact,"public_boundary":{"preflight":preflight,"run":run,"verify":verify,"cell_deadline_seconds":cell_deadline_seconds,"category_remaining_at_start_seconds":category_remaining}}
        import run_phase4_evaluation as evaluation
        classification=evaluation.classify_candidate(path,shot_id=cell["shot_id"],candidate=terminal.get("diagnostic_candidate"))
        selected=terminal.get("selection_status")=="frozen_decoder_visible_candidate"
        return {"cell_id":cell["cell_id"],"sample_namespace":observation["sample_namespace"],"sample_identity":observation["sample_identity"],"execution_status":"completed","terminal":True,**classification,"selected":selected,"candidate_origin":terminal.get("diagnostic_candidate_origin"),"raw_work":fact["work_vector"],"runtime_seconds":elapsed,"resource":{"maxrss_kib":None},"trace":trace,"artifact":artifact,"public_boundary":{"preflight":preflight,"run":run,"verify":verify,"cell_deadline_seconds":cell_deadline_seconds,"category_remaining_at_start_seconds":category_remaining}}
      except (OSError,RuntimeError,ValueError,subprocess.TimeoutExpired,TimeoutError) as error:
        elapsed=0.0 if began is None else perf_counter()-began; spent += elapsed
        trace=_retained_trace_evidence(active,root/"run",cell=cell,plan=plan)
        return {"cell_id":cell["cell_id"],"sample_namespace":cell["factorial_namespace"],"sample_identity":None,"execution_status":"incomplete_public_boundary","terminal":False,"failure":str(error),"raw_work":None,"runtime_seconds":elapsed,"resource":{"maxrss_kib":None},"trace":trace,"artifact":artifact,"public_boundary":{"cell_deadline_seconds":cell_deadline_seconds,"category_remaining_at_start_seconds":category_remaining}}
    return execute

def _result_status(gate, rows):
    if gate["development_fixture"]: return "development_fixture_not_assessed"
    return "completed_not_assessed" if all(row["execution_status"]=="completed" for row in rows) else "incomplete_or_inconclusive_not_assessed"

def run_factorial(*,evaluation_path,plan,executor:Callable[[Mapping[str,Any]],Mapping[str,Any]]|None=None,allow_development_fixture=False,repository_root:Path=ROOT,output_root:Path|None=None):
    gate=assert_factorial_predecessor(evaluation_path=evaluation_path,plan=plan,allow_development_fixture=allow_development_fixture); rows=[]
    if executor is None:
      if gate["development_fixture"] or output_root is None: raise ValueError("production public factorial execution requires a genuine predecessor and output root")
      executor=canonical_public_executor(repository_root=repository_root,output_root=output_root,plan=plan)
    for cell in plan["cells"]:
      actual=dict(executor(cell))
      if actual.get("cell_id")!=cell["cell_id"] or actual.get("sample_namespace")!=cell["factorial_namespace"]: raise ValueError("executor observation identity differs from factorial cell")
      rows.append({**actual,"code_id":cell["code_id"],"noise_region":cell["noise_region"],"shot_id":cell["shot_id"],"arm_id":cell["arm_id"]})
    cohorts=defaultdict(list)
    for row in rows: cohorts[(row["code_id"],row["noise_region"],row["shot_id"])].append(row)
    for cohort in cohorts.values():
      observed={row.get("sample_identity") for row in cohort if row.get("sample_identity") is not None}
      if len(observed)>1: raise ValueError("executor produced unmatched physical samples across factorial arms")
    validate_trace_inventory(rows,plan)
    status=_result_status(gate,rows)
    return {"schema_version":1,"status":status,"assessment":"not_assessed","predecessor":gate,"factorial_digest":plan["factorial_digest"],"terminals":rows,"trace_inventory":[{"cell_id":row["cell_id"],"code_id":row["code_id"],"noise_region":row["noise_region"],"arm_id":row["arm_id"],"shot_id":row["shot_id"],"execution_status":row["execution_status"],"trace":row.get("trace",{"status":"missing"})} for row in rows],"aggregate":aggregate_terminals(rows,plan)}
def trace_link_event(*,ledger_id,schedule):
    result=schedule.trace_result(); link=None if result is None else result.ledger_link()
    if link is None: raise ValueError("ordinary-memory trace yielded no sidecar link")
    return {"kind":"trace_link","ledger_id":ledger_id,"data":{"trace_kind":"ordinary_memory","sidecar":link}}
def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("--design",type=Path,default=ROOT/"data/evidence/phase4-pilot-design.json"); p.add_argument("--caps",type=Path,default=ROOT/"data/manifests/phase4-pilot-caps.json"); p.add_argument("--supplement",type=Path,default=ROOT/"data/evidence/phase4-factorial-execution-supplement-v1.json"); a=p.parse_args(); plan=build_factorial_plan(design=_read(a.design),caps=_read(a.caps),supplement=_read(a.supplement)); print(json.dumps({k:v for k,v in plan.items() if k!="cells"},indent=2,sort_keys=True))
if __name__=="__main__": main()
