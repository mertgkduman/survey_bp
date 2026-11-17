"""Static source evidence only; package absence/layout differences do not prove origin."""
import json
from pathlib import Path
import subprocess
import tomllib

P=Path('/tmp/survey-bp-priortilt-source-261113373')
R=Path('/tmp/survey-bp-relay-reference-261113373')
manifest=tomllib.loads((P/'decoder/Cargo.toml').read_text())
lock=tomllib.loads((P/'decoder/Cargo.lock').read_text())
packages=sorted(x['name'] for x in lock['package'])
assert not any('relay' in name.lower() for name in packages)
p=(P/'decoder/src/lib.rs').read_text();r=(R/'crates/relay_bp/src/bp/min_sum.rs').read_text()
assert 'macro_rules! make_core' in p and 'b2c: Vec<$t>' in p and 'SparseBipartiteGraph' not in p
assert 'check_to_variable: SparseBipartiteGraph<N>' in r and 'memory_strengths: Array1<N>' in r
assert 'let mut min_message' in r and 'let mut second_min_message' in r
assert 'let mut temp = inf' in p and 'if temp < cv' in p
history=subprocess.check_output(['git','-C',str(P),'log','--format=%h %s','--follow','--','decoder/src/lib.rs'],text=True)
initial=subprocess.check_output(['git','-C',str(P),'show','f7e209b:decoder/src/lib.rs'],text=True)
assert 'b2c: Vec<$t>' in initial and 'same arithmetic as the C++' in initial
result={'prior_commit':subprocess.check_output(['git','-C',str(P),'rev-parse','HEAD'],text=True).strip(),
        'relay_pinned_commit':subprocess.check_output(['git','-C',str(R),'rev-parse','HEAD'],text=True).strip(),
        'relay_current_head_checked':'cdfdc996ce55582c4c431f8d8392bcce57175e36',
        'relay_current_min_sum_git_blob':'4a0228574b34c4fb84c6969b8c8f2e77ca2c8e97',
        'prior_direct_dependencies':manifest['dependencies'],'relay_package_dependency_present':False,
        'prior_all_transitive_package_names':packages,'prior_rust_retained_history':history.splitlines(),
        'initial_source_layout_already_flat':True,'initial_comment_refers_to_unspecified_cpp':True,
        'observed':'separate compiled core with different graph representation and check-update implementation; both min-sum BP',
        'not_established':'whether authors consulted/copied/ported/rewrote Relay or any other earlier source; public history starts with a complete implementation',
        'scope':'static public-source inspection, not a forensic authorship proof or runtime comparison; current Relay has newer four-lane min-two optimization than pinned reference'}
(Path(__file__).parent/'evidence.json').write_text(json.dumps(result,indent=2)+'\n')
print('Verified no Relay package dependency and different structures; historical derivation remains unproven')
