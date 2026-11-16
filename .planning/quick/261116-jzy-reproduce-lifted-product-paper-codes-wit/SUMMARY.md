---
id: 261116-jzy
status: complete
campaign_status: running
implementation_commit: 53fabae
simulation_array: 61930050
audit_array: 61930127
collector: 61930188
workers_audited: 50
workers_planned: 72
phase_gates_changed: false
---

# Original lifted-product full stack launched

The user explicitly selected the original Panteleev–Kalachev paper, arXiv:2012.04068v2(2021 revision), rather than the later bias-tailored paper. Example4 gives LP(A,A*) with the published3x5 monomial matrix and lift31. The reconstructed code has n1054,k140, ranks457/457 and paired logical representatives. An independent coefficient-wise polynomial Kronecker expansion matches every check entry. No certified distance20 claim is made.

The original paper gives no LER curve, physical-rate grid or numeric cap for1054. This is a controlled depolarizing comparison at .02,.04,.06,.08,.10,.12. The32-iteration normalized-min-sum/.625 baseline is borrowed from the cited BP-OSD paper1904.02703v3. Its layered schedule differs from canonical flooding; there are no original LP curve ordinates to reproduce. Preserve this qualification in future reports.

Twelve arms at each of six rates: BP, Q-BP, binary BP+OSD0/CS10, correlated Q-BP+OSD0/CS10, tuned BP, tuned Q-BP, Relay32/128 and beam32/128. Binary arms decode both components under the same physical Pauli stream; joint BP uses correlated I/X/Y/Z beliefs. Joint OSD uses posterior marginals and original-component checks. All32 baseline graphs have equal maximum directed-edge work; the128 search arms are separately labelled4x work explorations. Canonical kernels and existing qualified OSD/search controllers are reused unchanged.

Damping, scale, offset and search settings receive512-shot coarse training and up to8192-shot/40-failure independent finalist training. LER wins; exact ties prefer mean sweeps, then warmed time and configuration digest. Fresh third-seed confirmation stops at20 any-logical failures or100M shots. Both residual components and invalid-syndrome failures count. Record all attempted work, OSD operations, hashes and instrumented latency; METHOD-NOTES.md explicitly distinguishes provenance-instrumented latency from pure algorithm time.

Simulation array61930050 has72 one-CPU/3GiB single-threaded workers. Audit array61930127 also has one CPU per point, and collector61930188 has one CPU/16GiB. A scheduling-only receipt releases49 satisfied aftercorr tasks after verifying corresponding source completions0:0 and completion hashes; the full frozen scientific auditor and remaining dependencies are unchanged. No prior frozen sources/results/manifests, kernels, archivedv1, model/config preferences or phase counters/gates changed.

First snapshot:50/72 workers independently audited,50 fresh measurements,273,537 shots/1,000 logical failures and1,140 separate training settings. Every retained row's samples/outcomes/work/stopping/selection and both endpoints of each64-shot chunk pass. Public view428→440 curves,3134→3178 points,12→13 codes,0 circuits. The12 compatible LP curves contain44 points; six incompatible/singleton settings remain in full tables without being merged into display curves. All1520 preexisting raw series retain identical points. Pending points remain unavailable, and automatic audits/collection continue.

Before the new study, the prior automatic beam-frontier collector completed218/218 workers and642 fresh settings/271,658,248 shots. Its642 summary hashes and aggregate counts were independently reconciled and retained in separate commit9dba3da; raw evidence was preserved.

Validation:20 new scientific tests;61 unique scientific regressions across new/old stack;55 catalog/projection/display tests;16 distinct Chromium workflow groups, with the7 public groups repeated on the final published13-code snapshot. One repeat of an old runtime test passed its scientific assertions but failed NFS temporary-directory cleanup; the isolated retry passed unchanged. The original61-case run before that retry had60 passes. No product/source changes were made for that filesystem cleanup race.96 independent pilot shots cover all12 arms and remain separate from training/confirmation. Exact source/software/code pins still validate after dispatch. Code commit53fabae; data and GSD follow-up retain this running status.
