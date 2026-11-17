"""Keep frozen publisher intact while reporting the explicit CPU amendment."""
import json
import report
import run
import parallel


def collect():
    parallel.load_amendment()
    report.collect()
    path=run.ROOT/'RESULTS.md';text=path.read_text()
    text=text.replace('Each point uses one CPU for X/Z memories sequentially.',
        'The original workers used one CPU; remaining points continue under the ten-CPU resource amendment, sharing one process pool across the X/Z memory runs.')
    text+='''\nResource history: `resource-amendment.json` binds the unchanged scientific plan to `parallel.py` and ten CPUs per remaining point. Original prefixes are preserved. Sealed batches may compute ahead; only the exact ordered stopping prefix enters this table. Extra work is retained separately in each point's `parallel-work.json`, with all sealed speculative candidates independently audited. Original single-CPU and concurrent ten-CPU timing cohorts should be analyzed separately; pooled mean decoder time is not a standalone single-CPU benchmark. Interrupted work before a sealed stage has no measured counter.\n'''
    path.write_text(text)


if __name__=='__main__':collect()
