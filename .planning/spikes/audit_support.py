"""Small reproducible evidence recorder; no production decoding implementation."""
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import importlib.metadata
import json
import subprocess
import traceback
import numpy as np

ROOT = Path(__file__).resolve().parents[2]

def serial(value):
    if isinstance(value, np.ndarray): return value.tolist()
    if isinstance(value, np.generic): return value.item()
    if isinstance(value, Path): return str(value)
    raise TypeError(type(value).__name__)

class Audit:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.events = []

    def record(self, name, passed, **details):
        self.events.append(dict(name=name, passed=bool(passed), **details))

    def probe(self, name, function):
        try:
            details = function()
            self.record(name, True, details=details)
        except Exception as exc:
            self.record(name, False, exception=type(exc).__name__, detail=str(exc),
                        traceback=traceback.format_exc())

    def finish(self):
        sources = sorted((ROOT / 'src/bp_registry').rglob('*.py'))
        hashes = {str(p.relative_to(ROOT)): sha256(p.read_bytes()).hexdigest() for p in sources}
        packages = {}
        for name in ('numpy', 'scipy', 'numba', 'ldpc', 'pytest'):
            try: packages[name] = importlib.metadata.version(name)
            except importlib.metadata.PackageNotFoundError: packages[name] = None
        summary = dict(schema='canonical_kernel_audit_v1',
                       timestamp_utc=datetime.now(timezone.utc).isoformat(),
                       git_head=subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip(),
                       packages=packages, source_hashes=hashes,
                       checks=len(self.events), passed=sum(e['passed'] for e in self.events),
                       failed=sum(not e['passed'] for e in self.events), events=self.events)
        target = self.directory / 'results.json'
        target.write_text(json.dumps(summary, indent=2, default=serial, allow_nan=False)+'\n')
        print(json.dumps({k:summary[k] for k in ('checks','passed','failed')}))
        for event in self.events:
            if not event['passed']: print('FINDING:', event['name'], event.get('detail', ''))
        return summary
