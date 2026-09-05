"""The mutation-sweep tree lock must be observed refusing things (BLUA-11 / ADR-046 §4).

The lock is a guard, so it is subject to the rule it exists to serve: a passing check counts
only if it could have failed. A lock never observed refusing anything is not evidence that it
locks — and the failure mode it was ruled in to prevent (F-2) was one where every check in the
sweep reported green while the results were wrong.

So the refusals here are driven by *real* holders in *real* subprocesses, not by a stubbed
liveness probe:

* a live holder is a process that is genuinely running and has genuinely taken the lock;
* a dead holder is that same process ``SIGKILL``-ed mid-hold, which is the shape of the two
  recorded mid-sweep crashes (F-0, F-3) — it cannot release, so it leaves the lock behind.

Every refusal test is paired with a control showing the same call path succeeds when the
condition is absent. Without the control, a lock that refused unconditionally would pass the
refusal tests, and "it refused" would carry no information.
"""

from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import signal
import subprocess
import sys
import time

import pytest

REPO = pathlib.Path(__file__).resolve().parent.parent
MODULE_PATH = REPO / "scripts" / "mutation_tree_lock.py"


def _load():
    spec = importlib.util.spec_from_file_location("mutation_tree_lock", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    # Register before exec: dataclasses resolve their own __module__ at class-creation time.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


tl = _load()


# --------------------------------------------------------------------------------------
# A real holder in a real process.
# --------------------------------------------------------------------------------------

_HOLDER_SOURCE = """
import importlib.util, sys, time
spec = importlib.util.spec_from_file_location("mutation_tree_lock", {module!r})
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)
lock = m.TreeLock({tree!r}, {run_id!r}, lock_root={root!r})
lock.acquire()
print("ACQUIRED", flush=True)
time.sleep(600)
"""


class _Holder:
    """A subprocess that really holds the lock until it is killed or terminated."""

    def __init__(self, tree, lock_root, run_id="holder-run"):
        source = _HOLDER_SOURCE.format(
            module=str(MODULE_PATH), tree=str(tree), run_id=run_id, root=str(lock_root)
        )
        self.proc = subprocess.Popen(
            [sys.executable, "-c", source], stdout=subprocess.PIPE, text=True
        )
        assert self.proc.stdout is not None
        line = self.proc.stdout.readline().strip()
        assert line == "ACQUIRED", f"holder failed to take the lock: {line!r}"

    @property
    def pid(self) -> int:
        return self.proc.pid

    def kill_without_releasing(self) -> None:
        """SIGKILL: the holder cannot run cleanup, so the lock file survives it."""
        self.proc.send_signal(signal.SIGKILL)
        self.proc.wait(timeout=10)
        # The pid must actually be gone before liveness is judged, or "dead" would be a race.
        for _ in range(100):
            if tl.process_start_time(self.proc.pid) is None:
                return
            time.sleep(0.02)
        pytest.fail(f"holder pid {self.proc.pid} still resolvable after SIGKILL")

    def stop(self) -> None:
        if self.proc.poll() is None:
            self.proc.kill()
            self.proc.wait(timeout=10)


@pytest.fixture
def tree(tmp_path):
    d = tmp_path / "checkout-a"
    d.mkdir()
    return d


@pytest.fixture
def lock_root(tmp_path):
    return tmp_path / "locks"


# --------------------------------------------------------------------------------------
# 1. Exclusivity, and that it is scoped to the tree rather than to the harness.
# --------------------------------------------------------------------------------------


def test_a_second_sweep_against_a_live_held_tree_is_refused(tree, lock_root):
    """(a) of the falsifiability requirement, demonstrated against a genuinely live holder."""
    holder = _Holder(tree, lock_root)
    try:
        with pytest.raises(tl.LockHeld) as caught:
            tl.TreeLock(tree, "second-run", lock_root=lock_root).acquire()
    finally:
        holder.stop()

    assert caught.value.holder.pid == holder.pid
    assert caught.value.holder.run_id == "holder-run"
    assert "LIVE" in str(caught.value)


def test_the_same_call_succeeds_once_the_holder_is_gone(tree, lock_root):
    """Control for the test above: the refusal is conditional on a live holder, not blanket.

    A lock that refused every acquisition would pass the refusal test and be useless. This is
    what makes that test's pass informative.
    """
    holder = _Holder(tree, lock_root)
    with pytest.raises(tl.LockHeld):
        tl.TreeLock(tree, "second-run", lock_root=lock_root).acquire()

    holder.proc.terminate()
    holder.proc.wait(timeout=10)
    # The killed holder leaves its file behind; clear it as the procedure requires.
    tl.clear_stale(tree, verified_against="test-fixture", cleared_by="test", lock_root=lock_root)

    got = tl.TreeLock(tree, "second-run", lock_root=lock_root).acquire()
    assert got.run_id == "second-run"


def test_a_sweep_on_another_tree_is_not_blocked(tree, tmp_path, lock_root):
    """The ruling is a per-tree lock, not a global harness lock.

    This fails against a single shared lock file, which is the obvious wrong implementation.
    """
    other = tmp_path / "checkout-b"
    other.mkdir()

    holder = _Holder(tree, lock_root)
    try:
        got = tl.TreeLock(other, "other-tree-run", lock_root=lock_root).acquire()
        assert got.tree == str(other.resolve())
        assert tl.lock_file_for(tree, lock_root) != tl.lock_file_for(other, lock_root)
    finally:
        holder.stop()


def test_two_checkouts_with_the_same_directory_name_get_different_locks(tmp_path, lock_root):
    a = tmp_path / "one" / "repo"
    b = tmp_path / "two" / "repo"
    a.mkdir(parents=True)
    b.mkdir(parents=True)
    assert tl.lock_file_for(a, lock_root) != tl.lock_file_for(b, lock_root)


def test_only_one_of_many_racing_acquirers_wins(tree, lock_root):
    """Exclusivity under an actual race, not merely under sequential calls."""
    source = f"""
import importlib.util, sys
spec = importlib.util.spec_from_file_location("mutation_tree_lock", {str(MODULE_PATH)!r})
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)
try:
    m.TreeLock({str(tree)!r}, sys.argv[1], lock_root={str(lock_root)!r}).acquire()
    print("WON")
except m.TreeLockError:
    print("REFUSED")
"""

    procs = [
        subprocess.Popen(
            [sys.executable, "-c", source, f"racer-{i}"], stdout=subprocess.PIPE, text=True
        )
        for i in range(8)
    ]
    outs = [p.communicate(timeout=60)[0].strip() for p in procs]
    assert outs.count("WON") == 1, outs


# --------------------------------------------------------------------------------------
# 2. Liveness: a dead holder is identifiable as dead.
# --------------------------------------------------------------------------------------


def test_a_lock_left_by_a_crashed_sweep_is_stale_not_live(tree, lock_root):
    """(b) of the falsifiability requirement.

    Same tree, same acquire call, same lock file as the live case above — the only thing that
    changed is whether the holder is still running, and the outcome is a different exception
    type. That is the distinction the ruling asks the lock to make: without it, F-0 and F-3
    would each have wedged every later audit behind a manual file deletion.
    """
    holder = _Holder(tree, lock_root)
    holder.kill_without_releasing()

    with pytest.raises(tl.StaleLockIncident) as caught:
        tl.TreeLock(tree, "next-run", lock_root=lock_root).acquire()

    assert caught.value.liveness == "dead"
    assert caught.value.holder is not None
    assert caught.value.holder.pid == holder.pid
    assert tl.inspect(tree, lock_root)["state"] == "stale"


def test_live_and_stale_are_different_verdicts_not_one_refusal(tree, lock_root):
    """The two refusals must not collapse into a single 'locked' error.

    They demand opposite responses: wait, versus verify the tree against version control. A
    lock that raised one type for both would pass every other test in this file.
    """
    holder = _Holder(tree, lock_root)
    live_state = tl.inspect(tree, lock_root)
    with pytest.raises(tl.LockHeld):
        tl.TreeLock(tree, "x", lock_root=lock_root).acquire()

    holder.kill_without_releasing()
    dead_state = tl.inspect(tree, lock_root)
    with pytest.raises(tl.StaleLockIncident):
        tl.TreeLock(tree, "x", lock_root=lock_root).acquire()

    assert live_state["state"] == "live" and live_state["liveness"] == "live"
    assert dead_state["state"] == "stale" and dead_state["liveness"] == "dead"
    assert live_state["holder"] == dead_state["holder"], (
        "the payload did not change; only the holder's liveness did"
    )
    assert not issubclass(tl.LockHeld, tl.StaleLockIncident)
    assert not issubclass(tl.StaleLockIncident, tl.LockHeld)


def test_a_recycled_pid_does_not_read_as_live(tree, lock_root):
    """Liveness is pid *and* process start time.

    A pid-only check — ``os.kill(pid, 0)`` — reports live as soon as the number is reissued to
    any unrelated process, and the stale lock then never expires. Here the recorded start time
    is wrong while the pid is this very test process, so it is unambiguously alive: a pid-only
    implementation returns "live" and this assertion fails.
    """
    holder = tl.Holder(
        tree=str(tree),
        run_id="ghost",
        pid=os.getpid(),
        hostname=tl.socket.gethostname(),
        proc_start="Thu Jan  1 00:00:00 1970",
        user="",
        acquired_at="1970-01-01T00:00:00+00:00",
    )
    assert tl.process_start_time(os.getpid()) is not None, "this process must be alive"
    assert tl.classify(holder) == "dead"


def test_a_holder_on_another_host_is_unknown_not_live(tree, lock_root):
    holder = tl.Holder(
        tree=str(tree),
        run_id="elsewhere",
        pid=os.getpid(),
        hostname="some-other-machine",
        proc_start="whenever",
        user="",
        acquired_at="1970-01-01T00:00:00+00:00",
    )
    assert tl.classify(holder) == "unknown"


def test_a_holder_with_no_recorded_start_time_is_unknown_not_live(tree, lock_root):
    """Refusing to judge on the pid alone when the start time was never captured."""
    holder = tl.Holder(
        tree=str(tree),
        run_id="partial",
        pid=os.getpid(),
        hostname=tl.socket.gethostname(),
        proc_start="",
        user="",
        acquired_at="1970-01-01T00:00:00+00:00",
    )
    assert tl.classify(holder) == "unknown"


def test_an_unreadable_lock_is_an_incident_not_a_silent_overwrite(tree, lock_root):
    """A truncated lock is itself an integrity signal and must not be treated as absent."""
    lock_file = tl.lock_file_for(tree, lock_root)
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    lock_file.write_text("{ this is not json", encoding="utf-8")

    with pytest.raises(tl.StaleLockIncident) as caught:
        tl.TreeLock(tree, "next-run", lock_root=lock_root).acquire()
    assert caught.value.holder is None
    assert caught.value.liveness == "unknown"
    assert lock_file.exists()


# --------------------------------------------------------------------------------------
# 3. A stale lock is a tree-integrity incident, not a file to delete.
# --------------------------------------------------------------------------------------


def test_refusing_a_stale_lock_does_not_remove_it(tree, lock_root):
    """The refusal must leave the evidence in place for the incident procedure."""
    holder = _Holder(tree, lock_root)
    holder.kill_without_releasing()
    lock_file = tl.lock_file_for(tree, lock_root)

    with pytest.raises(tl.StaleLockIncident):
        tl.TreeLock(tree, "next-run", lock_root=lock_root).acquire()
    assert lock_file.exists(), "a stale lock is not self-clearing"

    with pytest.raises(tl.StaleLockIncident):
        tl.TreeLock(tree, "next-run", lock_root=lock_root).acquire()
    assert lock_file.exists()


def test_clearing_without_a_version_control_verification_is_refused(tree, lock_root):
    """The tree must be verified against version control *before* the next sweep starts.

    F-3 was produced by exactly the improvised step this refuses: deleting the leftover and
    carrying on.
    """
    holder = _Holder(tree, lock_root)
    holder.kill_without_releasing()
    lock_file = tl.lock_file_for(tree, lock_root)

    with pytest.raises(tl.TreeLockError, match="verified_against"):
        tl.clear_stale(tree, verified_against="   ", cleared_by="qa-lead", lock_root=lock_root)
    assert lock_file.exists()


def test_clearing_without_a_named_clearer_is_refused(tree, lock_root):
    holder = _Holder(tree, lock_root)
    holder.kill_without_releasing()
    lock_file = tl.lock_file_for(tree, lock_root)

    with pytest.raises(tl.TreeLockError, match="cleared_by"):
        tl.clear_stale(tree, verified_against="49b472c", cleared_by="", lock_root=lock_root)
    assert lock_file.exists()


def test_clearing_records_the_incident_before_removing_the_lock(tree, lock_root):
    """Control for the two refusals above, and the durable-record requirement."""
    holder = _Holder(tree, lock_root)
    holder.kill_without_releasing()
    lock_file = tl.lock_file_for(tree, lock_root)

    record = tl.clear_stale(
        tree,
        verified_against="49b472c",
        cleared_by="qa-lead",
        note="stranded mutation check",
        lock_root=lock_root,
    )
    assert not lock_file.exists()

    written = [
        json.loads(line)
        for line in (lock_root / "incidents.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(written) == 1
    assert written[0]["verified_against"] == "49b472c"
    assert written[0]["cleared_by"] == "qa-lead"
    assert written[0]["liveness"] == "dead"
    assert written[0]["holder"]["pid"] == holder.pid
    assert record["kind"] == "stale-lock-incident"

    # And the tree is now acquirable, so the procedure actually unblocks the next sweep.
    assert tl.TreeLock(tree, "next-run", lock_root=lock_root).acquire().run_id == "next-run"


def test_clearing_a_live_lock_is_refused(tree, lock_root):
    """Clearing is not an eviction route for a running sweep."""
    holder = _Holder(tree, lock_root)
    try:
        with pytest.raises(tl.LockHeld):
            tl.clear_stale(
                tree, verified_against="49b472c", cleared_by="qa-lead", lock_root=lock_root
            )
        assert tl.lock_file_for(tree, lock_root).exists()
    finally:
        holder.stop()


# --------------------------------------------------------------------------------------
# 4. Release.
# --------------------------------------------------------------------------------------


def test_release_refuses_to_remove_another_holders_lock(tree, lock_root):
    holder = _Holder(tree, lock_root)
    try:
        impostor = tl.TreeLock(tree, "not-mine", lock_root=lock_root)
        with pytest.raises(tl.NotLockOwner):
            impostor.release()
        assert tl.lock_file_for(tree, lock_root).exists()
    finally:
        holder.stop()


def test_the_context_manager_releases_on_the_way_out(tree, lock_root):
    lock_file = tl.lock_file_for(tree, lock_root)
    with tl.TreeLock(tree, "run-1", lock_root=lock_root) as held:
        assert lock_file.exists()
        assert held.run_id == "run-1"
    assert not lock_file.exists()
    tl.TreeLock(tree, "run-2", lock_root=lock_root).acquire()


def test_the_context_manager_releases_when_the_sweep_raises(tree, lock_root):
    """A crashing sweep inside the block must not leave the tree locked."""
    lock_file = tl.lock_file_for(tree, lock_root)
    with pytest.raises(RuntimeError):
        with tl.TreeLock(tree, "run-1", lock_root=lock_root):
            raise RuntimeError("sweep blew up")
    assert not lock_file.exists()


def test_locks_are_not_stored_in_run_scratch(tree):
    """F-0 lost its restore copies to ``PAPERCLIP_RUN_SCRATCH_DIR``, which Paperclip deletes.

    A lock kept there would vanish at exactly the moment a crashed run most needs to have left
    a trace, and the crash would be indistinguishable from a clean exit.
    """
    default = str(tl.DEFAULT_LOCK_ROOT)
    assert "scratch" not in default.lower()
    assert not default.startswith("/tmp")
    assert str(pathlib.Path(tl.lock_file_for(tree)).parent) == default
