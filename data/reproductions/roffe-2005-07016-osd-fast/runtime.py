"""Versioned compiled traversal; reuse the frozen audited OSD event protocol."""
import importlib.util
import os
from pathlib import Path

from bp_registry.postprocessing.canonical_bp import PreparedRoffeBp, VERSION as BP_VERSION

SOURCE = Path(__file__).resolve().parent.with_name('roffe-2005-07016-osd') / 'runtime.py'
spec = importlib.util.spec_from_file_location('_roffe_osd_fast_event_protocol', SOURCE)
execution = importlib.util.module_from_spec(spec)
spec.loader.exec_module(execution)
original_state = execution.state


class PreparedState(tuple):
    """Retain the original tuple contract and one immutable controller binding."""


def state(job):
    base, processor = original_state(job)
    base = PreparedState(base)
    base.prepared = PreparedRoffeBp(base)
    return base, processor


def decode_bp(base, syndrome):
    return base.prepared.decode(syndrome)


class Ledger(execution.Ledger):
    def commit(self, rows):
        # Keep checkpoints resumable before filesystem exhaustion. All workers
        # write at most one bounded 4096-shot chunk after this shared-space check.
        space = os.statvfs(SOURCE.parent)
        if space.f_bavail*space.f_frsize < 50*1024**3:
            raise RuntimeError('less than 50 GiB free; preserve checkpoint and resume after storage is available')
        return super().commit(rows)


# Bind only this isolated module instance. The frozen scalar runtime and every
# earlier campaign retain their own original controller and source identities.
execution.state, execution.decode_bp = state, decode_bp
execution.Ledger = Ledger
rt, VERSION, BATCH = execution.rt, execution.VERSION, execution.BATCH
event, warm, execute, collect = execution.event, execution.warm, execution.execute, execution.collect
