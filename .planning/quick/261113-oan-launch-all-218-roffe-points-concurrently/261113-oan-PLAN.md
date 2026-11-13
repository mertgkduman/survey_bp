# Launch Roffe with one CPU for every point

GSD quick --validate, executed inline. Latest user instruction supersedes the
old16-point scheduling cap and serial wait for MacKay. Scientific specifications
remain frozen:218 points, one worker per point, source grids, min-sum settings,
T=n,20 failures/100M stop, identical seeds and artifacts.

1. Add an execution-only launcher beside the frozen Roffe runner. Verify the
   frozen plan and workers=1, request218 one-CPU tasks, cap concurrency218,
   constrain native math threads to1, preserve logs and source runner arguments.
2. Use the existing dispatch lock and dispatch.json array/collect receipt keys.
   Original MacKay continuation must see those same accepted jobs and submit
   nothing twice. Preserve its eventual complete audit/publication duties and
   keep the live MacKay worker running.
3. Test resource arguments, complete-array collector dependency, receipt reuse
   by both new and frozen launchers, and recovery from partial submission.
   Run scheduler preflight, commit launch code, dispatch, verify accepted slots
   and startup states, record GSD status, commit/push receipts.

The old frozen run.py/README.md/plan.json are not edited; LAUNCH-ALL.md records
the user's scheduling override. This task completes when dispatch is verified;
scientific measurements and final complete-ledger audit remain asynchronous.
