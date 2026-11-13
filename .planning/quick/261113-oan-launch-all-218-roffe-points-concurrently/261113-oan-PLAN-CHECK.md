# Plan check — pass

The scientific runner's source is pinned by multiple active studies. A new
execution-only launcher changes Slurm arguments without changing frozen files.
All218 jobs already specify workers=1, so218 array slots means218 CPUs, plus
4 still-running MacKay CPUs. Normal math libraries remain single-threaded.
The user association ceiling is400 CPUs; current user allocation is6 slots
including the2-CPU session, so the requested launch fits that known ceiling.

Shared existing lock/receipt keys make the frozen original submitter a no-op
once this launcher records the array and collector. Keep the MacKay advance
alive to finish its own audits; no pending job needs cancellation. Require
all218 terminal results for final audit/publication. Do not claim scientific
completion from accepted scheduling or startup.
