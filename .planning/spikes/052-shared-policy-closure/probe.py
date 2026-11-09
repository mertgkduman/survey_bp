"""Composition/admission, controller invariants, and operand-liveness audit."""
from pathlib import Path
from itertools import product
from unittest.mock import patch
import importlib.util
import json
import sys
import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(HERE.parent))
from audit_support import Audit
from bp_registry.canonical.policy_decoder import BinaryPolicy,BinaryPolicyDecoder
from bp_registry.canonical.contracts import MemoryCompositionSpec
from bp_registry.canonical.memory_execution import LocalMemoryExecution
from bp_registry.policy_capabilities import capability_inventory

spec=importlib.util.spec_from_file_location('shared_fixtures',ROOT/'tests/canonical/test_shared_policy_decoder.py')
fixtures=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixtures)


def matrix():
    h=np.array([[1,1,1,0],[1,1,1,0],[0,1,0,1]],np.uint8)
    prior=np.array([1.7,-.8,2.3,.4])
    schedules=['flooding','layered','check_node_serial','variable_node_serial','group_shuffled','residual']
    memories=[None,'affine_prior','v2c_damping','pdbp_field_mix','pdprime_delta_mix','posterior_momentum']
    records=[];accepted=0;shots=0
    for schedule,rule,kind,backend in product(schedules,['spa','min_sum','normalized_min_sum','offset_min_sum'],memories,['auto','scalar','compiled']):
        expected=(schedule not in ['group_shuffled','residual'] or (rule=='spa' and kind is None))
        expected &= backend!='compiled' or (schedule=='flooding' and kind is None)
        kwargs=dict(schedule=schedule,rule=rule,backend=backend,max_iterations=2,
                    partitions=((0,),(1,),(2,)) if schedule=='layered' else None,
                    memory=None if kind is None else fixtures.memory(kind,local=schedule!='flooding'))
        entry=dict(schedule=schedule,rule=rule,memory=kind,backend=backend,expected_admission=expected)
        try:
            decoder=BinaryPolicyDecoder(h,BinaryPolicy(**kwargs))
        except ValueError as exc:
            assert not expected,(entry,str(exc))
            records.append(dict(entry,admitted=False,reason=str(exc)));continue
        assert expected,entry
        accepted+=1
        rows=[]
        for bits in [[0,0,0],[0,1,0],[1,0,1],[1,1,1]]:
            result=decoder.decode(bits,prior_llrs=prior)
            assert result.converged==np.array_equal(h@result.candidate % 2,bits)
            assert decoder.verify_ledger(result.ledger_json)
            assert decoder.decode(bits,prior_llrs=prior).ledger_json==result.ledger_json
            detail=result.ledger['execution']
            if 'leaves' in detail:
                leaves=detail['leaves']
                assert len({leaf[0] for leaf in leaves})==len(leaves)
                assert {key:sum(leaf[2][key] for leaf in leaves) for key in detail['work']}==detail['work']
            rows.append(dict(syndrome=bits,candidate=result.candidate.tolist(),converged=result.converged,iterations=result.iterations))
            shots+=1
        records.append(dict(entry,admitted=True,shots=rows))
    (HERE/'matrix.json').write_text(json.dumps(records,indent=2)+'\n')
    (HERE/'capabilities.json').write_text(json.dumps(capability_inventory(),indent=2)+'\n')
    return dict(configurations=len(records),accepted=accepted,rejected=len(records)-accepted,primary_shots=shots,
                repeated_and_replay_shots=2*shots)


def controllers():
    records=[]
    graphs=[np.array([[1,1,1,0],[0,1,0,1]],np.uint8),np.ones((2,4),np.uint8)]
    priors=[[1.2,2.,.4,1.8],[1.2,-2.,.4,-1.8],[-.8,.5,-1.2,2.3]]
    for graph,kind,prior,bits in product(range(2),fixtures.CONTROLLERS,priors,product([0,1],repeat=2)):
        decoder=BinaryPolicyDecoder(graphs[graph],BinaryPolicy(controller=kind,options=fixtures.CONTROLLERS[kind]))
        result=decoder.decode(bits,prior_llrs=prior)
        assert result.converged==np.array_equal(graphs[graph]@result.candidate % 2,bits)
        assert decoder.verify_ledger(result.ledger_json)
        if result.ledger['execution']['selection_succeeded']:
            assert result.converged,(kind,prior,bits)
        records.append(dict(graph=graph,controller=kind,prior=prior,syndrome=list(bits),
            candidate=result.candidate.tolist(),converged=result.converged,iterations=result.iterations))
    (HERE/'controllers.json').write_text(json.dumps(records,indent=2)+'\n')
    return dict(cases=len(records),controllers=len(fixtures.CONTROLLERS),graphs=[x.tolist() for x in graphs])


def combined_memory(schedule,alpha):
    affine=fixtures.memory('affine_prior',local=True).model_dump(mode='json')['bindings'][0]
    affine.update(binding_id='affine',history_owner='affine-history',parameters={'alpha':alpha})
    delta=fixtures.memory('pdprime_delta_mix',local=True).model_dump(mode='json')['bindings'][0]
    delta.update(binding_id='delta',history_owner='delta-history',order=1)
    return MemoryCompositionSpec.model_validate(dict(bindings=[affine,delta]))


def local_fixed_prior_admission():
    records=[]
    original=LocalMemoryExecution.transform_beliefs
    h=np.array([[1,1,1],[1,1,1]],np.uint8)
    for schedule in ['layered','check_node_serial','variable_node_serial']:
        results=[]
        for alpha in [0.,.9]:
            observed=[]
            def spy(self,fresh,c2v):
                output=original(self,fresh,c2v)
                observed.append(dict(fresh=fresh.tolist(),output=output.tolist()))
                return output
            with patch.object(LocalMemoryExecution,'transform_beliefs',spy):
                decoder=BinaryPolicyDecoder(h,BinaryPolicy(schedule=schedule,max_iterations=4,
                    partitions=((0,),(1,)) if schedule=='layered' else None,memory=combined_memory(schedule,alpha)))
                result=decoder.decode([0,1],prior_llrs=[.8,-1.3,2.])
            results.append(dict(alpha=alpha,candidate=result.candidate.tolist(),observations=observed,
                memory=result.ledger['execution']['memory']))
        records.append(dict(schedule=schedule,runs=results,
            fresh_changed=any(a['fresh']!=b['fresh'] for a,b in zip(results[0]['observations'],results[1]['observations'])),
            all_outputs_identical=all(a['output']==b['output'] for a,b in zip(results[0]['observations'],results[1]['observations']))))
    (HERE/'fixed-prior-counterexample.json').write_text(json.dumps(records,indent=2)+'\n')
    assert not any(r['fresh_changed'] and r['all_outputs_identical'] for r in records), (
        'Local schedules admit affine prior before fixed-prior PD-prime; PD-prime discards its changed operand. '
        'Flooding already rejects this composition. See fixed-prior-counterexample.json.')
    return dict(cases=len(records))


def randomized_boundaries():
    records=[]
    h=np.ones((4,4),np.uint8)
    for scope,schedule in product(['configuration','attempt','sweep'],['layered','check_node_serial','variable_node_serial']):
        decoder=BinaryPolicyDecoder(h,BinaryPolicy(schedule=schedule,randomized=scope,max_iterations=3,
            partitions=((0,),(1,),(2,),(3,)) if schedule=='layered' else None))
        a=decoder.decode([0,1,0,1],prior_llrs=[1.,-.8,.6,-1.1],shot_identity='shot-a')
        b=decoder.decode([0,1,0,1],prior_llrs=[1.,-.8,.6,-1.1],shot_identity='shot-b')
        one=a.ledger['execution']['orders'];two=b.ledger['execution']['orders']
        assert len(one)==(3 if scope=='sweep' else 1)
        if scope=='configuration':assert one==two
        for item in one+two:assert sorted(item['order'])==[0,1,2,3]
        assert a.iterations==12 and b.iterations==12
        records.append(dict(scope=scope,schedule=schedule,first=one,second=two))
    (HERE/'randomized-boundaries.json').write_text(json.dumps(records,indent=2)+'\n')
    return dict(cases=len(records))


if __name__=='__main__':
    audit=Audit(HERE)
    audit.probe('ordinary_composition_matrix',matrix)
    audit.probe('controller_original_problem_invariants',controllers)
    audit.probe('randomized_refresh_boundaries',randomized_boundaries)
    audit.probe('local_fixed_prior_composition_admission',local_fixed_prior_admission)
    audit.finish()
