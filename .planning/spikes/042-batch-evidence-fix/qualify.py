"""Replay immutable historical counterexamples into new evidence directories."""
from pathlib import Path
import importlib.util
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from audit_support import Audit


def load(number, name, filename='probe.py'):
    source = next(HERE.parent.glob(f'{number:03d}-*')) / filename
    spec = importlib.util.spec_from_file_location(f'qualification_{number}_{name}', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.HERE = HERE / name
    module.HERE.mkdir(exist_ok=True)
    return module


def main():
    math = load(34, 'mathematics')
    native = load(35, 'native')
    policies = load(36, 'policies')
    grid = load(36, 'grid', 'grid.py')
    boundaries = load(37, 'boundaries')
    audit = Audit(HERE)
    for name, function in (
        ('exact_tree_inference', math.randomized_trees),
        ('graph_covariance', math.graph_covariance),
        ('deterministic_domain_exclusion', math.deterministic_prior_boundary),
        ('native_heterogeneous_alignment', native.heterogeneous_native),
        ('compiled_policy_grid', grid.grid),
        ('DEM_affine_parity_projection', boundaries.dem_semantics),
        ('factory_validation_control', boundaries.valid_boundary_controls),
        ('compiled_graph_ownership_control', boundaries.compiled_ownership_control),
        ('unmodified_batch_ledger_control', boundaries.ledger_control),
    ):
        audit.probe(name, function)
        print(name, audit.events[-1]['passed'], flush=True)
    policies.indexed_updates(audit)
    policies.reported_posterior(audit)
    boundaries.circuit_admission(audit)
    boundaries.ownership(audit)
    boundaries.batch_evidence(audit)
    result = audit.finish()
    assert result['failed'] == 0


if __name__ == '__main__':
    main()
