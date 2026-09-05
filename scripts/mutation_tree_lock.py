"""Exclusive per-tree lock for mutation-testing sweeps (BLUA-11 Board ruling, ADR-046 §4).

A mutation sweep edits source files in place and restores them. Two sweeps against the same
tree interleave their mutations and restores, and the damage is silent: in the BLUA-8 audit
(F-2) a second, orphaned harness produced *confidently wrong* verdicts — sites credited
``GUARD-FIRED`` on the strength of failures in tests that never touch the mutated module, and a
"pristine" copy snapshotted while a guard was already neutralised, then verified against itself.
Every contaminated site reported ``restore_green=True``. Nothing inside either sweep's own
output could reveal it.

What this module provides, and the three properties the ruling asks for:

1. **Exclusivity scoped to the tree under mutation, not to the harness.** The lock file is
   keyed on the resolved path of the tree, so a sweep on one checkout never blocks a sweep on
   another. Acquisition is an ``O_EXCL`` create: exactly one process wins.

2. **Holder liveness recorded in the lock.** The payload carries run id, pid, hostname and the
   holder process's start time. A lock left behind by a crashed sweep is therefore
   *identifiable as dead*, rather than indistinguishable from a live one. Without this, the two
   recorded mid-sweep crashes (F-0, F-3) would wedge every later audit behind a manual file
   deletion — which is exactly the undocumented improvised step that produced F-3.

3. **A stale lock is a tree-integrity incident, not a file to delete.** A cooperative lock
   stops a second sweep from *starting*; it does not stop an orphaned mutator that is already
   past its check — F-2's second harness outlived the run that started it. So finding a stale
   lock means the tree may carry a stranded mutation, and clearing it goes through
   :func:`clear_stale`, which refuses without a recorded version-control verification and
   writes an incident record before the file is removed. The procedure is in
   ``scripts/mutation_tree_lock.md``.

Both refusal paths refuse. The distinction between them is about what the operator must do
next, and it is the reason ``LockHeld`` and ``StaleLockIncident`` are separate types rather
than one error with a flag.

**Threat-model note.** A sweep must never mutate the lock's own implementation, or the guard
could be neutralised by the thing it is guarding. Callers should assert their mutation target
list excludes this file; the BLUA-8 harness does so before acquiring.
"""

from __future__ import annotations

import getpass
import hashlib
import json
import os
import socket
import subprocess
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

DEFAULT_LOCK_ROOT = Path.home() / ".paperclip" / "qa-audits" / ".tree-locks"
"""Locks live outside every tree and outside ``PAPERCLIP_RUN_SCRATCH_DIR``.

Run scratch is deleted at run end. F-0 lost its restore copies exactly that way; a lock stored
there would vanish at the moment a crashed run most needs to have left a trace.
"""

Liveness = Literal["live", "dead", "unknown"]

_READ_RETRIES = 5
_READ_RETRY_SECONDS = 0.05


@dataclass(frozen=True)
class Holder:
    """Who claims to hold a tree lock, and enough about them to test the claim."""

    tree: str
    run_id: str
    pid: int
    hostname: str
    proc_start: str
    user: str
    acquired_at: str

    @classmethod
    def from_payload(cls, payload: dict) -> Holder:
        return cls(
            tree=str(payload["tree"]),
            run_id=str(payload["run_id"]),
            pid=int(payload["pid"]),
            hostname=str(payload["hostname"]),
            proc_start=str(payload.get("proc_start", "")),
            user=str(payload.get("user", "")),
            acquired_at=str(payload.get("acquired_at", "")),
        )


class TreeLockError(Exception):
    """Base for every refusal this module raises."""


class LockHeld(TreeLockError):
    """The tree is locked by a holder that is still running. Wait; do not intervene."""

    def __init__(self, holder: Holder, lock_file: Path) -> None:
        self.holder = holder
        self.lock_file = lock_file
        super().__init__(
            f"tree {holder.tree} is locked by a LIVE sweep: run={holder.run_id} "
            f"pid={holder.pid} on {holder.hostname} since {holder.acquired_at} "
            f"(lock: {lock_file}). Refusing to start."
        )


class StaleLockIncident(TreeLockError):
    """A lock with no live holder. This is a tree-integrity incident, not a stuck file.

    Carries ``holder`` (``None`` when the lock file could not be parsed) and the liveness
    verdict, so the incident report can state *why* the holder was judged not live.
    """

    def __init__(
        self, holder: Holder | None, liveness: Liveness, lock_file: Path, tree: Path
    ) -> None:
        self.holder = holder
        self.liveness = liveness
        self.lock_file = lock_file
        self.tree = tree
        who = (
            f"run={holder.run_id} pid={holder.pid} on {holder.hostname} since {holder.acquired_at}"
            if holder
            else "unreadable lock payload"
        )
        super().__init__(
            f"tree {tree} carries a STALE lock ({liveness}): {who} (lock: {lock_file}). "
            "A sweep that ended without releasing may have left a stranded mutation, and an "
            "orphaned mutator past its own check is not stopped by this lock. Verify the tree "
            "against version control, then clear via clear_stale(); do NOT delete the file. "
            "See scripts/mutation_tree_lock.md."
        )


class NotLockOwner(TreeLockError):
    """Refusing to release or clear a lock this process does not own."""


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def lock_file_for(tree: Path, lock_root: Path | None = None) -> Path:
    """The lock file for one tree.

    Keyed on the *resolved* tree path, so the scope is the tree under mutation and sweeps on
    other trees stay concurrent. The basename keeps the directory name for a human reading
    ``ls``, and a path digest for uniqueness — two checkouts of the same repo in differently
    named parents must not collide, and two with the same name in different parents must not
    either.
    """
    resolved = Path(tree).resolve()
    digest = hashlib.sha256(str(resolved).encode("utf-8")).hexdigest()[:16]
    root = Path(lock_root) if lock_root is not None else DEFAULT_LOCK_ROOT
    return root / f"{resolved.name}-{digest}.lock"


def process_start_time(pid: int) -> str | None:
    """The start time of ``pid``, or ``None`` if no such process exists.

    The pid alone is not enough: pids are recycled, so a dead sweep's pid can later belong to
    an unrelated live process and the lock would read as live forever. Comparing the start time
    recorded at acquisition against the start time now distinguishes "still the same process"
    from "that number was reissued".
    """
    try:
        result = subprocess.run(
            ["ps", "-o", "lstart=", "-p", str(pid)],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    start = result.stdout.strip()
    return start or None


def classify(holder: Holder, *, hostname: str | None = None) -> Liveness:
    """Is this holder still running?

    ``unknown`` is deliberately not a synonym for ``dead``: a lock written on another host, or
    one whose holder we cannot identify precisely, must not be silently reclaimed. Both
    ``dead`` and ``unknown`` route to :class:`StaleLockIncident` — the difference is what the
    incident report has to say.
    """
    here = hostname if hostname is not None else socket.gethostname()
    if holder.hostname != here:
        return "unknown"
    current = process_start_time(holder.pid)
    if current is None:
        return "dead"
    if not holder.proc_start:
        # The holder's start time was never captured, so a recycled pid is indistinguishable
        # from the original. Refuse to call it live on the pid alone.
        return "unknown"
    return "live" if current == holder.proc_start else "dead"


def read_lock(lock_file: Path) -> Holder | None:
    """Read a lock's holder, or ``None`` if the file is absent or unreadable.

    A lock is created with ``O_EXCL`` and written immediately after, so a reader can catch it
    empty in the microseconds between. Retrying separates that benign race from a genuinely
    truncated file, which is itself an integrity signal and must survive to be reported.
    """
    for attempt in range(_READ_RETRIES):
        try:
            raw = lock_file.read_text(encoding="utf-8")
        except FileNotFoundError:
            return None
        except OSError:
            return None
        if raw.strip():
            try:
                return Holder.from_payload(json.loads(raw))
            except (ValueError, KeyError, TypeError):
                return None
        if attempt < _READ_RETRIES - 1:
            time.sleep(_READ_RETRY_SECONDS)
    return None


def inspect(tree: Path, lock_root: Path | None = None) -> dict:
    """State of a tree's lock, for the stale-lock procedure and for reporting.

    Never mutates anything. Returns ``state`` of ``unlocked`` / ``live`` / ``stale``.
    """
    lock_file = lock_file_for(tree, lock_root)
    if not lock_file.exists():
        return {"state": "unlocked", "lock_file": str(lock_file), "holder": None, "liveness": None}
    holder = read_lock(lock_file)
    if holder is None:
        return {
            "state": "stale",
            "lock_file": str(lock_file),
            "holder": None,
            "liveness": "unknown",
            "reason": "unreadable lock payload",
        }
    liveness = classify(holder)
    return {
        "state": "live" if liveness == "live" else "stale",
        "lock_file": str(lock_file),
        "holder": asdict(holder),
        "liveness": liveness,
    }


class TreeLock:
    """An exclusive lock on one tree for the duration of a mutation sweep.

    Use as a context manager. ``acquire`` either returns the holder record it wrote, or raises:
    :class:`LockHeld` when a live sweep owns the tree, :class:`StaleLockIncident` when a lock
    exists with no live holder. It never takes a lock away from anyone.
    """

    def __init__(
        self,
        tree: Path,
        run_id: str,
        *,
        lock_root: Path | None = None,
        pid: int | None = None,
        hostname: str | None = None,
    ) -> None:
        self.tree = Path(tree).resolve()
        self.run_id = run_id
        self.lock_root = Path(lock_root) if lock_root is not None else DEFAULT_LOCK_ROOT
        self.lock_file = lock_file_for(self.tree, self.lock_root)
        self.pid = pid if pid is not None else os.getpid()
        self.hostname = hostname if hostname is not None else socket.gethostname()
        self.holder: Holder | None = None

    def _payload(self) -> Holder:
        try:
            user = getpass.getuser()
        except (KeyError, OSError):
            user = ""
        return Holder(
            tree=str(self.tree),
            run_id=self.run_id,
            pid=self.pid,
            hostname=self.hostname,
            proc_start=process_start_time(self.pid) or "",
            user=user,
            acquired_at=_now(),
        )

    def acquire(self) -> Holder:
        """Take the lock, or refuse. Never steals, never deletes."""
        self.lock_root.mkdir(parents=True, exist_ok=True)
        holder = self._payload()
        try:
            fd = os.open(self.lock_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        except FileExistsError:
            existing = read_lock(self.lock_file)
            if existing is None:
                raise StaleLockIncident(None, "unknown", self.lock_file, self.tree) from None
            liveness = classify(existing, hostname=self.hostname)
            if liveness == "live":
                raise LockHeld(existing, self.lock_file) from None
            raise StaleLockIncident(existing, liveness, self.lock_file, self.tree) from None
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(asdict(holder), fh, indent=2, sort_keys=True)
            fh.write("\n")
            fh.flush()
            os.fsync(fh.fileno())
        self.holder = holder
        return holder

    def release(self) -> None:
        """Release a lock this process owns. Refuses to remove anyone else's."""
        current = read_lock(self.lock_file)
        if current is None:
            self.holder = None
            return
        if current.run_id != self.run_id or current.pid != self.pid:
            raise NotLockOwner(
                f"refusing to release {self.lock_file}: held by run={current.run_id} "
                f"pid={current.pid}, this process is run={self.run_id} pid={self.pid}"
            )
        self.lock_file.unlink(missing_ok=True)
        self.holder = None

    def __enter__(self) -> Holder:
        return self.acquire()

    def __exit__(self, exc_type, exc, tb) -> Literal[False]:
        self.release()
        return False


def clear_stale(
    tree: Path,
    *,
    verified_against: str,
    cleared_by: str,
    note: str = "",
    lock_root: Path | None = None,
) -> dict:
    """Close out a stale lock as a tree-integrity incident, then remove the lock file.

    ``verified_against`` is the version-control reference the tree was checked against before
    this call — the whole point of the ruling is that the tree is verified *before* the next
    sweep starts, so a call with nothing to record is refused rather than accepted with a blank
    field. The incident is appended to ``incidents.jsonl`` before the file is unlinked, so a
    crash between the two leaves the record, not the silence.

    Refuses outright if the holder is live: clearing is not a way to evict a running sweep.
    """
    if not verified_against.strip():
        raise TreeLockError(
            "clear_stale requires verified_against: the version-control reference the tree was "
            "verified against before the next sweep. A stale lock means a sweep ended without "
            "releasing and may have left a stranded mutation; deleting the file without that "
            "check is the improvised step this procedure exists to replace."
        )
    if not cleared_by.strip():
        raise TreeLockError(
            "clear_stale requires cleared_by: a gate with no named clearer is not reviewed."
        )

    lock_file = lock_file_for(tree, lock_root)
    if not lock_file.exists():
        raise TreeLockError(f"no lock to clear at {lock_file}")

    holder = read_lock(lock_file)
    liveness: Liveness = "unknown" if holder is None else classify(holder)
    if liveness == "live":
        assert holder is not None
        raise LockHeld(holder, lock_file)

    record = {
        "kind": "stale-lock-incident",
        "recorded_at": _now(),
        "tree": str(Path(tree).resolve()),
        "lock_file": str(lock_file),
        "holder": asdict(holder) if holder else None,
        "liveness": liveness,
        "verified_against": verified_against,
        "cleared_by": cleared_by,
        "note": note,
    }
    root = lock_file.parent
    root.mkdir(parents=True, exist_ok=True)
    incidents = root / "incidents.jsonl"
    with incidents.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, sort_keys=True) + "\n")
        fh.flush()
        os.fsync(fh.fileno())
    lock_file.unlink()
    record["incidents_log"] = str(incidents)
    return record


def _main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description="Inspect or clear a mutation-sweep tree lock.")
    ap.add_argument("command", choices=["inspect", "clear"])
    ap.add_argument("--tree", required=True)
    ap.add_argument("--lock-root", default=None)
    ap.add_argument("--verified-against", default="", help="VCS ref the tree was verified against")
    ap.add_argument("--cleared-by", default="", help="named clearer")
    ap.add_argument("--note", default="")
    a = ap.parse_args(argv)

    root = Path(a.lock_root) if a.lock_root else None
    if a.command == "inspect":
        print(json.dumps(inspect(Path(a.tree), root), indent=2, sort_keys=True))
        return 0
    try:
        print(
            json.dumps(
                clear_stale(
                    Path(a.tree),
                    verified_against=a.verified_against,
                    cleared_by=a.cleared_by,
                    note=a.note,
                    lock_root=root,
                ),
                indent=2,
                sort_keys=True,
            )
        )
    except TreeLockError as exc:
        print(f"REFUSED: {exc}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
