"""Static surface inventory; import references are not execution coverage."""
from pathlib import Path
from hashlib import sha256
import ast,json
ROOT=Path.cwd();HERE=Path(__file__).parent
imports={}
for p in sorted(Path('tests').rglob('*.py')):
    tree=ast.parse(p.read_text())
    for node in ast.walk(tree):
        if isinstance(node,ast.ImportFrom) and node.module:
            imports.setdefault(node.module,set()).add(str(p))
        elif isinstance(node,ast.Import):
            for alias in node.names:imports.setdefault(alias.name,set()).add(str(p))
rows=[]
for p in sorted(Path('src/bp_registry').rglob('*.py')):
    tree=ast.parse(p.read_text());module='.'.join(p.with_suffix('').parts[1:]);module=module.removesuffix('.__init__')
    rows.append(dict(module=module,path=str(p),sha256=sha256(p.read_bytes()).hexdigest(),
        description=ast.get_docstring(tree),
        definitions=[dict(name=n.name,line=n.lineno,kind=type(n).__name__) for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))],
        direct_test_imports=sorted(imports.get(module,())),
        qualification='inventory only; imports do not prove branch, equation or composition coverage'))
(HERE/'source-inventory.json').write_text(json.dumps(rows,indent=2)+'\n')
print(json.dumps(dict(modules=len(rows),modules_with_direct_test_imports=sum(bool(r['direct_test_imports']) for r in rows))))
