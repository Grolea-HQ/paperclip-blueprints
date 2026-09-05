# Stale-lock procedure — mutation-testing sweeps

Companion to `scripts/mutation_tree_lock.py`. Board ruling BLUA-11 (`local-board`, 2026-09-05,
adopt as amended), recorded in ADR-046 §4 and Consequences.

This exists because the step it replaces was improvised. F-3 entered a run to find a stranded
mutation in the working tree with no surviving copy; the leftover was cleared and the run
continued. Nothing recorded what the tree was verified against, and nothing said whether the
mutator that stranded it was still running. That is the gap this document closes.

---

## The rule in one line

**A stale lock is a tree-integrity incident, not a file to delete.**

A cooperative lock stops a second sweep from *starting*. It does not stop an orphaned mutator
that is already past its own check — F-2's second harness outlived the run that started it.
So a lock with no live holder means two things may be true at once: the tree may carry a
stranded mutation, and something may still be writing to it.

## What the harness does on its own

| Situation | Harness | Exit |
|---|---|---|
| No lock | acquires, sweeps, releases | 0 |
| Lock held by a **live** holder | refuses; `LockHeld` | 2 |
| Lock with **no live** holder (dead, unknown host, unreadable) | refuses; `StaleLockIncident` | 3 |

Neither refusal deletes anything. Clearing is a separate, deliberate act — this procedure.

Liveness is pid **and** process start time, both recorded in the lock at acquisition. Pids are
recycled; a pid-only check reports live as soon as the number is reissued, and the lock would
then never be clearable except by hand — reintroducing the very step that produced F-3.

---

## Procedure

Run every step. Do not skip step 3 because the tree "looks clean" — a neutralised guard is a
one-line edit that changes no line numbers, which is exactly what it was designed to be.

### 1. Read the lock

```bash
uv run python scripts/mutation_tree_lock.py inspect --tree "$TREE"
```

Record `holder.run_id`, `holder.pid`, `holder.hostname`, `holder.acquired_at`, and `liveness`.
If `state` is `live`, **stop** — this is not a stale lock. Wait for that sweep, or find its
operator. Clearing is not an eviction route and `clear_stale` refuses a live holder.

### 2. Establish that no mutator is still running

```bash
ps -p "<holder.pid>"                     # expect: no such process
pgrep -fl 'harness.py|mutation_tree_lock' # expect: nothing but your own shell
```

If anything matches, you have F-2's situation — a second harness on a shared tree. Do not
clear. Escalate to Head of Engineering, identify the process's run, and stop it before going
further. Any sweep that overlapped it is discarded, not repaired: its verdicts are
cross-attributed and its own output cannot reveal that.

If `liveness` was `unknown` rather than `dead` — a lock written on another host, or one whose
holder start time was never captured — you cannot establish this from `ps` alone. Say so in the
`--note` at step 5 rather than recording a check you did not perform.

### 3. Verify the tree against version control

This is the step the ruling turns on: the tree is verified **before the next sweep starts**,
not after it produces results.

```bash
git status --porcelain                   # untracked/modified files
git diff --stat                          # any content drift
git stash list                           # a mutation parked rather than restored
```

Then, specifically for the sweep's own mutation marker:

```bash
grep -rn 'MUTATED-' --include='*.py' src/ scripts/ || echo "no mutation markers"
```

(`--include='*.py'` keeps this file, which quotes the marker, out of its own results — a
procedure that always reports a hit teaches the reader to ignore the hit.)

Decide and record one of:

- **Tree clean** — `git status` empty and no markers. Note the commit SHA; that is your
  `--verified-against`.
- **Stranded mutation found** — restore the affected file from the audit's baseline copy
  (`~/.paperclip/qa-audits/<audit>/baseline/`), not from `git checkout`. Restoring from version
  control is a protocol deviation: it is recorded as cleanup, and **no guard is credited** on
  any sweep that relied on it. Re-run the suite and confirm green before continuing.
- **Unexpected uncommitted work** — not the sweep's doing. Leave it, and name it in the note;
  the next sweep's baseline must be taken from a tree you can describe.

### 4. Read the journal of the interrupted sweep

`records.jsonl` in the audit directory. Every mutation is journalled *before* it is applied, so
the last `about-to-mutate` record with no matching `complete` record names the site the crash
left behind. Cross-check it against what step 3 found. A disagreement between the two is itself
a finding — report it; do not reconcile it silently.

### 5. Clear, with the verification on the record

```bash
uv run python scripts/mutation_tree_lock.py clear \
  --tree "$TREE" \
  --verified-against "<commit SHA from step 3>" \
  --cleared-by "<named clearer>" \
  --note "<what step 2/3/4 found>"
```

Both `--verified-against` and `--cleared-by` are required; the call is refused if either is
blank. A gate with no named clearer is not reviewed, and a clear with no verification reference
is the improvised deletion this procedure replaces. The incident is appended to
`incidents.jsonl` beside the lock **before** the lock file is unlinked, so a crash between the
two leaves the record rather than silence.

### 6. Only then, start the sweep

```bash
uv run python ~/.paperclip/qa-audits/<audit>/harness.py snapshot   # fresh baseline copies
uv run python ~/.paperclip/qa-audits/<audit>/harness.py sweep --release "<SHA>"
```

Take the baseline copies **after** step 3, never before. F-2's second harness snapshotted its
"pristine" copy while a guard was already neutralised, then verified each restore by comparing
that copy against itself — an identical-sides comparison inside the audit instrument, and every
contaminated site still reported `restore_green=True`.

---

## Reporting

A cleared incident is not a closed finding. Include in the sweep's report:

- the incident record from `incidents.jsonl`, verbatim;
- whether a stranded mutation was found, and how it was restored;
- if version control was used to restore, the explicit statement that no guard is credited on
  that basis.

## Scope limits — what this does not cover

- **The lock does not protect the lock.** A sweep against `mutation_tree_lock.py` itself cannot
  be guarded by it. The BLUA-14 sweep of this module ran single-process and sequential, and
  asserted the tree byte-identical to the copy before and after each mutation instead.
- **Cooperative only.** Any process not going through `TreeLock` is unaffected. The lock makes
  a concurrent sweep *detectable and refused at start*; it does not make one impossible.
- **One host.** A lock from another hostname classifies as `unknown` and refuses. Cross-host
  concurrent sweeps on a shared filesystem are out of scope and would need a different design.
