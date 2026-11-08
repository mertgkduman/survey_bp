"""Current backend differential and public receipt integrity audit."""
from importlib.util import spec_from_file_location,module_from_spec
from pathlib import Path
import json,tempfile
from audit_support import Audit,ROOT
from bp_registry.canonical.numerics import BINARY_SPA_F64_V3
from bp_registry.quaternary.numerics import QBP4_F64_V3
from bp_registry.runner import run_quaternary,verify_quaternary_run

HERE=Path(__file__).parent
spec=spec_from_file_location('old_execution_probe',HERE.parent/'011-execution-consistency/probe.py')
old=module_from_spec(spec);spec.loader.exec_module(old)
old.BINARY_SPA_F64_V2=BINARY_SPA_F64_V3
old.QBP4_F64_V2=QBP4_F64_V3

def receipts(a):
    source=ROOT/'.planning/spikes/011-execution-consistency/quaternary_experiment_v3-budget-counterexample/input.json'
    data=json.loads(source.read_text());data['schema_version']='quaternary_experiment_v4';data.pop('numerical_profile',None)
    with tempfile.TemporaryDirectory(prefix='v3-receipt-audit-') as temporary:
        root=Path(temporary);manifest=root/'input.json';manifest.write_text(json.dumps(data))
        out=root/'out';result=run_quaternary(manifest,out)
        assert verify_quaternary_run(out)['verified']
        a.record('untampered_public_v4_replays',True,work=result['work'],committed_sweeps=result['committed_sweeps'])
        modifications={'termination':'fabricated_terminal','outcome':'fabricated_outcome','numerical_profile':'fabricated_profile','run_fidelity':'fabricated_fidelity'}
        rows=[]
        for field,replacement in modifications.items():
            tampered=dict(result);tampered[field]=replacement
            (out/'result.json').write_text(json.dumps(tampered))
            try:accepted=bool(verify_quaternary_run(out)['verified']);reason=None
            except ValueError as exc:accepted=False;reason=str(exc)
            rows.append(dict(field=field,original=result.get(field),replacement=replacement,accepted_as_verified=accepted,rejection=reason))
        a.record('V3-A03_public_verification_rejects_false_summary_fields',not any(x['accepted_as_verified'] for x in rows),counterexamples=rows,
            scope='result.json summaries; unchanged ledger remains byte-identical and correct')
        tampered=json.loads(json.dumps(result));tampered['work']['bp_calls']+=1
        (out/'result.json').write_text(json.dumps(tampered))
        try:verify_quaternary_run(out);rejected=False
        except ValueError:rejected=True
        a.record('public_work_tamper_rejected',rejected)

if __name__=='__main__':
    a=Audit(HERE)
    a.probe('frozen_v1_and_current_v3_full_buffer_differentials',old.buffer_differentials)
    receipts(a)
    a.finish()
