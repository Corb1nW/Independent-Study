"""Shared run-manifest support for model runs (D-055 item C1).

A run manifest ties a model run to an exact commit and to the bytes of every
file it consumed. This module holds the parts that do not depend on a
particular model, so the Phase B hip model and later models (Phase D) build
manifests the same way.

Per consumed input the manifest records:

- ``sha256``: SHA-256 of the raw bytes read at run time. Platform-dependent:
  a Windows checkout with CRLF line endings gives a different value than a
  Linux checkout of the same commit.
- ``git_blob_id``: the Git object ID of the file at ``HEAD``. Platform-
  independent: the same commit gives the same ID on every checkout (Phase B
  re-review note N4). ``None`` when the run is not in a Git checkout.

Validity is stated as fixed facts about what the run is. A manifest never
asserts its own review state; reviews of ``commit_sha`` are recorded in
``docs/DECISIONS.md`` and ``PROJECT_STATE.md``.
"""
import hashlib
import json
import subprocess
from pathlib import Path

VERIFIED = "verified_git_head_and_inputs"
UNVERIFIED_ARCHIVE = "caller_supplied_sha_unverified_archive_or_no_git"

VALIDITY = {
    "kind": "software demonstration of a data-to-dynamics path",
    "physiological_validity": "not established",
    "clinical_validity": "not established",
    "review_state": ("not asserted by this manifest; see docs/DECISIONS.md and "
                     "PROJECT_STATE.md for reviews and acceptance of commit_sha"),
}


def file_hash(path):
    """SHA-256 of the raw bytes of ``path``."""
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check_commit_sha(commit_sha):
    if not isinstance(commit_sha, str) or len(commit_sha) != 40 or any(
            ch not in "0123456789abcdef" for ch in commit_sha):
        raise ValueError("exact 40-character commit SHA required")
    return commit_sha


def _git(root, *args):
    return subprocess.run(["git", *args], cwd=root, capture_output=True, check=True)


def verify_inputs(root, paths, commit_sha, *, expected_hashes=None):
    """Check every consumed file against ``HEAD`` and describe it.

    Returns ``(status, records)``. ``records`` maps each input name to
    ``{"path", "sha256", "git_blob_id"}``.

    In a Git checkout this fails closed: the checkout root and ``HEAD`` must
    match ``commit_sha``, and every input must be a tracked file inside the
    repository whose Git-filtered content equals the committed object. Git's
    filters are used for that comparison, so a clean Windows CRLF checkout
    passes (Phase B finding D1). ``expected_hashes`` additionally pins the raw
    bytes read when the inputs were resolved.

    Without Git metadata (an archive) nothing can be verified: the status says
    so, blob IDs are ``None`` and paths are recorded as given.
    """
    root = Path(root).resolve()
    expected_hashes = expected_hashes or {}
    if not (root / ".git").exists():
        records = {}
        for name, value in paths.items():
            path = Path(value).resolve()
            current = path.read_bytes()
            if name in expected_hashes and hashlib.sha256(current).hexdigest() != expected_hashes[name]:
                raise ValueError(f"{name}: changed since input resolution")
            relative = (path.relative_to(root).as_posix()
                        if path.is_relative_to(root) else str(path))
            records[name] = {"path": relative,
                             "sha256": hashlib.sha256(current).hexdigest(),
                             "git_blob_id": None}
        return UNVERIFIED_ARCHIVE, records
    try:
        actual_root = Path(_git(root, "rev-parse", "--show-toplevel").stdout.decode().strip()).resolve()
        head = _git(root, "rev-parse", "HEAD").stdout.decode().strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ValueError("cannot verify Git checkout provenance") from exc
    if actual_root != root or head != commit_sha:
        raise ValueError("Git root or HEAD differs from claimed snapshot")
    records = {}
    for name, value in paths.items():
        path = Path(value).resolve()
        if not path.is_relative_to(root):
            raise ValueError(f"{name}: input path outside repository: {path}")
        relative = path.relative_to(root).as_posix()
        try:
            committed_oid = _git(root, "rev-parse", f"HEAD:{relative}").stdout.decode().strip()
            working_oid = _git(root, "hash-object", "--", relative).stdout.decode().strip()
            current = path.read_bytes()
        except (OSError, subprocess.CalledProcessError) as exc:
            raise ValueError(f"{name}: not a readable tracked input at HEAD: {relative}") from exc
        if working_oid != committed_oid:
            raise ValueError(f"{name}: working file differs from HEAD: {relative}")
        raw = hashlib.sha256(current).hexdigest()
        if name in expected_hashes and raw != expected_hashes[name]:
            raise ValueError(f"{name}: changed since input resolution")
        records[name] = {"path": relative, "sha256": raw, "git_blob_id": committed_oid}
    return VERIFIED, records


def manifest_header(root, paths, commit_sha, *, expected_hashes=None):
    """Fields every model run manifest starts with."""
    check_commit_sha(commit_sha)
    status, records = verify_inputs(root, paths, commit_sha,
                                    expected_hashes=expected_hashes)
    return {
        "validity": dict(VALIDITY),
        "commit_sha": commit_sha,
        "commit_provenance_status": status,
        "verified_input_files": sorted(paths) if status == VERIFIED else [],
        "inputs": records,
    }


def serialize_manifest(value):
    return json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
