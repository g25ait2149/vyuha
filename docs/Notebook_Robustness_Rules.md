# Notebook Robustness Rules — build every compute notebook against ALL these failure modes

A compute notebook is not "done" until it survives every item below on EVERY platform it can run on (Kaggle AND Colab). Derived from real losses (Lessons L6-L15). Enforce in code, not comments. Helper: `vyuha/cascade/runtime.py` (`persistent_out`, `finalize`).

## 1. Output persistence (the one that cost us two runs)
- **Invariant:** outputs land on PERSISTENT storage, verified BEFORE any long compute, on every platform.
- **Kaggle:** `/kaggle/working` persists ONLY in a committed (Batch) run. Detect `os.environ['KAGGLE_KERNEL_RUN_TYPE']`; if != 'Batch', **RAISE** with "use Save & Run All (Commit)". Never run long compute in an interactive/draft session.
- **Colab:** `/content` is wiped on runtime reclaim (incl. GPU-quota reclaim). Mount Google Drive and write there; if mount fails, **RAISE**.
- Retrieval instructions must be platform-correct: Kaggle Output tab / commit; Colab Drive; never Colab-only `files.download` on Kaggle.

## 2. Checkpoint + resume
- Save after every stage/shard to the persistent dir; on start, load and skip done work. A timeout/reset must RESUME, never restart. Long inner loops shard so a partial stage is not lost.

## 3. Visible progress
- Newline-terminated, flushed counters (not `\r` — line-based log viewers buffer it and look frozen). Every scorer prints progress, including intra-stage (not just "done").

## 4. Quota / cost
- Default to the minimum accelerator the code actually uses (single T4 unless genuinely multi-GPU; T4x2 doubles quota for no gain). Enforce hard $ caps in code for paid APIs. Prefer zero-compute re-analysis of saved data.

## 5. Data correctness (before scoring)
- Inspect real dataset STRUCTURE first (columns/dtypes/value-distributions; not harmful content). Reference columns explicitly; never auto-detect by name. ASSERT loaded counts > 0. Guard every scoring loop against empty inputs.

## 6. Stale code
- `git pull` does NOT update an already-imported Python module; restart the kernel after pulling. For fragile logic, fresh-clone + inline so neither cache nor a failed pull serves stale code.

## 7. Secrets / safety
- Secrets only from the platform Secrets store; never in code/logs. Keep the frozen components frozen; held-out conditions stay held out.

## 8. Self-reporting results (so a lost file never costs the answer)
- Persist the full output artifact (npz/json) to the persistent dir (rule 1) AND, at the end of the run, compute and PRINT the analysis-ready verdict/summary INLINE to the log (e.g. `tools/v7_analysis.main(OUTF)`). The decision is a handful of numbers — it must survive in the committed log independent of retrieving the large file. If the file is ever lost, the user can paste the printed verdict and we still have the result.

## Pre-run checklist (must all be true before starting a long run)
[ ] persistence guard raises on ephemeral storage  [ ] checkpoint+resume verified  [ ] newline progress incl. intra-stage
[ ] minimum accelerator  [ ] data structure inspected + counts asserted  [ ] empty-input guards  [ ] platform-correct retrieval  [ ] secrets/caps in place  [ ] verdict/summary printed inline + full output persisted
