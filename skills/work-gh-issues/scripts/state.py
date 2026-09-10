#!/usr/bin/env python3
"""Durable launch records and single-owner feedback checkpoints."""

from __future__ import annotations

import argparse
import copy
import fcntl
import json
import math
import os
import re
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path

VERSION = 1
DISPOSITIONS = {"required_now", "follow_up", "no_change", "needs_evidence"}
REQUIRED_NECESSITIES = {"acceptance", "introduced_regression", "safety", "required_gate"}
SHA = re.compile(r"[0-9a-f]{40}\Z")
IDENTITY = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*\Z")
ACTIVE_PHASES = {"plan", "implement", "review", "feedback", "publish"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def text(value):
    return isinstance(value, str) and bool(value.strip())


def strings(value, *, nonempty=True):
    return isinstance(value, list) and (bool(value) or not nonempty) and all(text(item) for item in value)


def state_directory():
    return Path(os.environ.get("WORK_GH_STATE_DIR", Path.home() / ".local/state/work-gh-issues")).expanduser().resolve()


@contextmanager
def locked(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(str(path) + ".lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError(f"state already has a writer: {path}") from exc
        yield
    finally:
        os.close(descriptor)


def validate_finding(finding):
    require(isinstance(finding, dict), "finding must be an object")
    for key in ("id", "claim", "file"):
        require(text(finding.get(key)), f"finding {key} is required")
    require(isinstance(finding.get("minimalAction"), str) and (finding.get("disposition") != "required_now" or text(finding["minimalAction"])), "finding minimalAction must be text and nonblank for required_now")
    for key in ("sourceIds", "affectedPremises", "evidenceRefs"):
        require(strings(finding.get(key)), f"finding {key} must contain evidence/identity strings")
    require(isinstance(finding.get("counterargument"), str), "finding counterargument is required")
    require(type(finding.get("line")) is int and finding["line"] > 0, "finding line must be positive")
    require(finding.get("severity") in {"blocker", "high", "medium", "low", "nit"}, "invalid finding severity")
    validity, necessity, disposition = (finding.get(key) for key in ("validity", "necessity", "disposition"))
    require(validity in {"valid", "invalid", "uncertain"}, "invalid factual validity")
    require(necessity in REQUIRED_NECESSITIES | {"optional", "none", "uncertain"}, "invalid feature necessity")
    require(disposition in DISPOSITIONS, "invalid finding disposition")
    allowed = {
        "required_now": validity == "valid" and necessity in REQUIRED_NECESSITIES,
        "follow_up": validity == "valid" and necessity == "optional",
        "no_change": validity == "invalid" or (validity == "valid" and necessity in {"none", "optional"}),
        "needs_evidence": validity != "invalid" and (validity == "uncertain" or necessity == "uncertain"),
    }
    require(allowed[disposition], "finding validity/necessity does not support its disposition")


def validate_targets(targets):
    require(isinstance(targets, dict), "target bindings must be an object")
    for ref, binding in targets.items():
        require(text(ref) and isinstance(binding, dict) and isinstance(binding.get("headSha"), str) and SHA.fullmatch(binding["headSha"]), "target requires an exact head SHA")
        require(all(isinstance(value, str) and SHA.fullmatch(value) for key, value in binding.items() if key.endswith(("Sha", "Oid"))), "target requires full SHAs/OIDs")


def validate_feedback(cursor):
    require(isinstance(cursor, dict) and isinstance(cursor.get("head_sha"), str) and SHA.fullmatch(cursor["head_sha"]), "feedback requires exact head")
    require(strings(cursor.get("required"), nonempty=False) and len(cursor["required"]) == len(set(cursor["required"])), "feedback requires explicit required sources")
    deadline = cursor.get("deadline")
    require(type(deadline) in {int, float} and math.isfinite(deadline) and deadline > 0, "feedback requires a bounded deadline")
    require(isinstance(cursor.get("results"), dict), "feedback results must be an object")
    for name, result in cursor["results"].items():
        require(text(name) and isinstance(result, dict) and result.get("status") in {"pending", "running", "passed", "failed"}, "invalid feedback result")
        require(isinstance(result.get("head_sha"), str) and SHA.fullmatch(result["head_sha"]), "feedback result requires exact head")


def validate(record):
    require(isinstance(record, dict) and record.get("version") == VERSION, "incompatible state version; preserve the file")
    require(record.get("kind") in {"batch", "owner", "batch_pointer"}, "invalid state kind")
    if record["kind"] == "batch_pointer":
        require(text(record.get("path")) and Path(record["path"]).is_absolute(), "invalid batch pointer")
        return record
    require(text(record.get("batch_id")) and IDENTITY.fullmatch(record["batch_id"]), "safe batch identity is required")
    if record["kind"] == "batch":
        for key in ("repository", "repo_path", "profile", "default_branch"):
            require(text(record.get(key)), f"batch {key} is required")
        for key in ("selected_issues", "launch_intents", "owners", "failures"):
            require(isinstance(record.get(key), list), f"batch {key} must be a list")
        selected = record["selected_issues"]
        require(selected and all(type(number) is int and number > 0 for number in selected) and len(selected) == len(set(selected)), "invalid selected issues")
        owned, identities, dependencies = [], [], {}
        for intent in record["launch_intents"]:
            require(isinstance(intent, dict) and text(intent.get("id")), "invalid launch owner identity")
            chain = intent.get("issues")
            require(isinstance(chain, list) and chain and all(type(number) is int and number > 0 for number in chain), "invalid owner chain")
            require(text(intent.get("owner_state")) and Path(intent["owner_state"]).is_absolute(), "owner state requires a durable absolute path")
            owned.extend(chain)
            identities.append(intent["id"])
            dependencies.update({str(child): parent for parent, child in zip(chain, chain[1:])})
        require(len(identities) == len(set(identities)) and len(owned) == len(set(owned)) and set(owned) == set(selected), "every selected issue needs exactly one chain owner")
        require(record.get("dependencies") == dependencies, "recorded dependencies must match the owner chains")
        return record
    for key in ("owner_id", "session_id", "phase"):
        require(text(record.get(key)), f"owner {key} is required")
    require(isinstance(record.get("chain"), list) and record["chain"] and all(type(n) is int and n > 0 for n in record["chain"]), "invalid owner chain")
    require(isinstance(record.get("feature_contract"), dict) and strings(record["feature_contract"].get("criteria")), "feature criteria are required")
    for key in ("findings", "repairs", "pushes", "targets", "evidence", "goal_binding", "feedback_cursor", "alternative_searches"):
        require(isinstance(record.get(key), dict), f"owner {key} must be an object")
    for key in ("repair_batches_used", "unchanged_attempts"):
        require(type(record.get(key)) is int and record[key] >= 0, f"invalid {key}")
    require(record["repair_batches_used"] == len(record["repairs"]) <= 2, "invalid repair accounting")
    require(isinstance(record.get("finding_history"), list), "invalid finding history")
    for identity, finding in record["findings"].items():
        validate_finding(finding)
        require(identity == finding["id"], "finding identity mismatch")
    validate_targets(record["targets"])
    for ref, cursor in record["feedback_cursor"].items():
        require(text(ref), "feedback ref is required")
        validate_feedback(cursor)
    outcome = record.get("outcome")
    require(outcome is None or isinstance(outcome, dict), "invalid workflow outcome")
    if outcome is not None:
        require(outcome.get("status") in {"review_ready", "stopped_blocked"} and text(outcome.get("reason")) and outcome.get("event_id") == f"{record['owner_id']}:{outcome['status']}", "invalid workflow outcome")
        require(record["phase"] == outcome["status"], "terminal phase/outcome mismatch")
    else:
        require(record["phase"] in ACTIVE_PHASES | {"repair"}, "invalid owner phase")
    return record


def load(path, kind=None):
    path = Path(path)
    require(not path.is_symlink(), f"state must not be a symlink: {path}")
    record = validate(json.loads(path.read_text(encoding="utf-8")))
    require(kind is None or record["kind"] == kind, f"expected {kind} state")
    return record


def save(path, record):
    validate(record)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as output:
            temporary = Path(output.name)
            json.dump(record, output, indent=2)
            output.write("\n")
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
        descriptor = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def register_batch(path, manifest):
    validate(manifest)
    pointer = state_directory() / "batches" / f"{manifest['batch_id']}.json"
    save(pointer, {"version": VERSION, "kind": "batch_pointer", "path": str(Path(path).resolve())})


def reserved_issues(repository, *, except_batch=None):
    numbers = set()
    for pointer in (state_directory() / "batches").glob("*.json"):
        manifest = load(load(pointer, "batch_pointer")["path"], "batch")
        if manifest["repository"].lower() == repository.lower() and manifest["batch_id"] != except_batch:
            numbers.update(manifest["selected_issues"])
    return numbers


def new_owner(owner_id, batch_id, session_id, chain, feature_contract):
    return validate({
        "version": VERSION, "kind": "owner", "owner_id": owner_id,
        "batch_id": batch_id, "session_id": session_id, "chain": chain,
        "feature_contract": feature_contract, "phase": "plan", "targets": {},
        "feedback_cursor": {}, "repair_batches_used": 0, "repairs": {},
        "active_repair": None, "unchanged_attempts": 0, "last_failure": "",
        "alternative_searches": {}, "findings": {}, "finding_history": [],
        "evidence": {}, "outcome": None, "goal_binding": {},
        "pushes": {}, "pending_push": None,
    })


def known_finding(record, claim):
    if claim["id"] in record["findings"]:
        return record["findings"][claim["id"]]
    return next((item for item in record["findings"].values() if all(item[key] == claim.get(key) for key in ("claim", "file", "affectedPremises"))), None)


def needs_adjudication(record, claim, *, requirements_changed=False, evidence_changed=False):
    require(type(requirements_changed) is bool and type(evidence_changed) is bool, "requirement/evidence changes must be explicit booleans")
    previous = known_finding(record, claim)
    return previous is None or requirements_changed or evidence_changed or any(previous[key] != claim.get(key) for key in ("claim", "affectedPremises"))


def reconcile_push(record, remote_shas):
    require(record["pending_push"] is not None, "no pending push intent")
    refs = record["pushes"][record["pending_push"]]["refs"]
    require(set(refs) == set(remote_shas), "remote observation must include every stack ref")
    if all(remote_shas[ref] == values["after"] for ref, values in refs.items()):
        return "already_pushed"
    if all(remote_shas[ref] == values["before"] for ref, values in refs.items()):
        return "retry_with_lease"
    raise ValueError("remote movement or partial stack push; do not replay history operations")


def feedback_status(record, ref, head_sha, *, now):
    cursor = record["feedback_cursor"].get(ref, {})
    if cursor.get("head_sha") != head_sha:
        return "stale"
    results = cursor["results"]
    if all(results.get(name, {}).get("head_sha") == head_sha and results[name].get("status") == "passed" for name in cursor["required"]):
        return "complete"
    if now >= cursor["deadline"] or any(results.get(name, {}).get("status") == "failed" for name in cursor["required"]):
        return "blocked"
    return "waiting"


def require_ready(record):
    evidence = record["evidence"]
    require(record["targets"] and evidence.get("targets") == record["targets"], "readiness requires current-target evidence")
    require(evidence.get("clean") is True and evidence.get("ancestry") is True, "readiness requires clean worktree and verified ancestry")
    require(strings(evidence.get("checks")), "readiness requires observed checks")
    require(all(strings(evidence.get("criteria", {}).get(item)) for item in record["feature_contract"]["criteria"]), "readiness requires evidence for every original criterion")
    review = evidence.get("review", {})
    contract = record["feature_contract"]
    review_required = not (contract.get("risk") == "low" and contract.get("review_required") is False)
    if review_required or review:
        require(review.get("complete") is True and strings(review.get("refs")), "readiness requires complete review evidence")
        focused = contract.get("risk") in {"low", "medium"} and contract.get("review_kind") == "focused" and not contract.get("canonical_abstraction_required")
        if focused:
            require(review.get("blocking") is False and review.get("verdict") != "EVADES", "focused review has no supported readiness assessment")
        else:
            require(review.get("verdict") in {"ALIGNED", "ALIGNED WITH FINDINGS"}, "readiness requires passing native canonical review evidence")
    if record["feedback_cursor"] or contract.get("feedback_required"):
        require(all(feedback_status(record, ref, binding["headSha"], now=time.time()) == "complete" for ref, binding in record["targets"].items()), "readiness requires completed feedback/checks for every current stack ref")
    for item in record["findings"].values():
        unresolved = not item.get("resolutionEvidence")
        require(not (unresolved and item["disposition"] == "required_now"), "unresolved required-now finding prevents readiness")
        critical = item["necessity"] in REQUIRED_NECESSITIES or (item["necessity"] == "uncertain" and item["severity"] in {"blocker", "high"})
        require(not (unresolved and item["disposition"] == "needs_evidence" and critical), "critical unresolved finding prevents readiness")
    require(record["active_repair"] is None and record["pending_push"] is None, "unfinished repair/push prevents readiness")


def apply(record, event, owner_id, session_id):
    validate(record)
    require(record["kind"] == "owner" and (record["owner_id"], record["session_id"]) == (owner_id, session_id), "owner/session writer mismatch")
    require(isinstance(event, dict) and text(event.get("type")), "event type is required")
    result = copy.deepcopy(record)
    kind = event["type"]
    if record["outcome"] is not None and kind != "goal_binding":
        require(kind == "outcome" and record["outcome"]["status"] == event.get("outcome") and record["outcome"]["reason"] == event.get("reason"), "owner is terminal; no automatic restart")
        return result
    if kind == "finding":
        item = copy.deepcopy(event["finding"])
        validate_finding(item)
        previous = known_finding(result, item)
        if previous:
            reopened = needs_adjudication(result, item, requirements_changed=event.get("requirements_changed", False), evidence_changed=event.get("evidence_changed", False))
            if reopened:
                active = result["repairs"].get(result["active_repair"], {})
                require(previous["id"] not in active.get("finding_ids", []), "active accepted claim set is frozen; defer the changed claim until this batch finishes")
                require(text(event.get("reason")), "reopening requires the changed premise or evidence")
                result["finding_history"].append({"finding": previous, "reason": event["reason"]})
            else:
                require(all(previous[key] == item[key] for key in ("validity", "necessity", "disposition")), "settled disposition needs reopening evidence")
                item = {**previous, "line": item["line"], "evidenceRefs": list(dict.fromkeys(previous["evidenceRefs"] + item["evidenceRefs"]))}
            item["id"] = previous["id"]
            item["sourceIds"] = list(dict.fromkeys(previous["sourceIds"] + event["finding"]["sourceIds"]))
        result["findings"][item["id"]] = item
    elif kind in {"resolve", "investigate", "follow_up"}:
        item = result["findings"][event["id"]]
        if kind == "follow_up":
            require(item["disposition"] == "follow_up" and text(event.get("ref")), "follow-up requires an optional concern and tracking reference")
            require(item.get("followUpRef", event["ref"]) == event["ref"], "reuse the existing deduplicated follow-up")
            item["followUpRef"] = event["ref"]
        else:
            require(strings(event.get("evidence")), "resolution/investigation evidence is required")
            if kind == "investigate":
                require(not item.get("investigationEvidence"), "one investigation per unchanged premise")
            item["resolutionEvidence" if kind == "resolve" else "investigationEvidence"] = event["evidence"]
    elif kind == "begin_repair":
        identity, ids = event["id"], event["finding_ids"]
        require(text(identity) and strings(ids) and len(ids) == len(set(ids)), "invalid accepted repair set")
        if identity in result["repairs"]:
            require(result["repairs"][identity]["finding_ids"] == ids, "repair set is frozen")
            return result
        require(result["active_repair"] is None, "finish the active repair before another accepted set")
        require(result["repair_batches_used"] < 2, "review repair budget exhausted")
        require(all(result["findings"][key]["disposition"] == "required_now" and not result["findings"][key].get("resolutionEvidence") for key in ids), "repair only unresolved required-now findings")
        result["repairs"][identity] = {"finding_ids": ids, "findings": {key: copy.deepcopy(result["findings"][key]) for key in ids}, "status": "active"}
        result["repair_batches_used"] += 1
        result["active_repair"], result["phase"] = identity, "repair"
    elif kind == "finish_repair":
        require(result["active_repair"] == event["id"], "repair is not active")
        repair = result["repairs"][event["id"]]
        require(all(result["findings"][key].get("resolutionEvidence") for key in repair["finding_ids"]), "repair findings still need resolution evidence")
        repair["status"] = "finished"
        result["active_repair"], result["phase"] = None, "review"
    elif kind == "attempt":
        failure = event["failure"]
        require(text(failure), "failure identity is required")
        if text(event.get("progress")):
            result["unchanged_attempts"] = 0
            result["last_progress"] = event["progress"]
        elif failure == result["last_failure"]:
            require(result["unchanged_attempts"] < 3, "three attempts without material progress exhausted")
            result["unchanged_attempts"] += 1
        else:
            result["unchanged_attempts"] = 1
        result["last_failure"] = failure
    elif kind == "alternative":
        require(text(event.get("doubt")), "alternative search requires concrete doubt")
        key = str(event["issue"])
        require(event["issue"] in result["chain"] and key not in result["alternative_searches"], "one alternative search per owned feature")
        result["alternative_searches"][key] = event["doubt"]
    elif kind == "phase":
        require(event.get("phase") in ACTIVE_PHASES and result["active_repair"] is None, "phase checkpoint cannot bypass an active repair or terminal readiness")
        result["phase"] = event["phase"]
    elif kind == "targets":
        validate_targets(event.get("targets"))
        require(event["targets"], "target bindings are required")
        result["targets"] = event["targets"]
        result["phase"] = "review"
    elif kind == "evidence":
        require(isinstance(event.get("evidence"), dict), "evidence must be an object")
        result["evidence"] = event["evidence"]
    elif kind == "feedback":
        validate_feedback(event)
        require(text(event.get("ref")), "feedback requires an exact ref")
        previous = result["feedback_cursor"].get(event["ref"])
        if previous:
            require(set(previous["required"]) <= set(event["required"]), "required feedback sources cannot disappear on resume")
            require(previous["head_sha"] != event["head_sha"] or previous["deadline"] == event["deadline"], "unchanged feedback head cannot extend its deadline")
        result["feedback_cursor"][event["ref"]] = {key: event[key] for key in ("head_sha", "required", "deadline", "results")}
        result["phase"] = "feedback"
    elif kind == "push_intent":
        identity, refs = event["id"], event["refs"]
        require(text(identity) and isinstance(refs, dict) and refs, "push identity and exact refs are required")
        for branch, binding in refs.items():
            require(text(branch) and isinstance(binding, dict) and SHA.fullmatch(binding.get("after", "")) and (binding.get("before") == "" or SHA.fullmatch(binding.get("before", ""))), "push requires full before/after SHAs (empty before only for new refs)")
        if identity in result["pushes"]:
            require(result["pushes"][identity]["refs"] == refs, "push intent cannot change after dispatch")
            return result
        require(result["pending_push"] is None, "reconcile the pending push first")
        require(identity == "initial" or identity in result["repairs"], "one push intent per accepted repair batch")
        result["pushes"][identity] = {"refs": refs, "status": "pending"}
        result["pending_push"] = identity
    elif kind == "push_observed":
        require(reconcile_push(result, event["remote_shas"]) == "already_pushed", "push not observed; retry only with the recorded lease")
        result["pushes"][result["pending_push"]]["status"] = "observed"
        result["pending_push"] = None
    elif kind == "goal_binding":
        binding = event["binding"]
        require(isinstance(binding, dict) and all(text(binding.get(key)) for key in ("owner_id", "pi_session_id", "goal_id")), "complete goal binding is required")
        require(binding["owner_id"] == owner_id, "goal owner mismatch")
        require(not result["goal_binding"] or all(binding[key] == result["goal_binding"][key] for key in ("owner_id", "pi_session_id", "goal_id")), "goal binding cannot silently change")
        result["goal_binding"] = binding
    elif kind == "outcome":
        require(event.get("outcome") in {"review_ready", "stopped_blocked"} and text(event.get("reason")), "terminal outcome requires an exact reason")
        if event["outcome"] == "review_ready":
            require_ready(result)
        result["outcome"] = {"status": event["outcome"], "reason": event["reason"], "event_id": f"{owner_id}:{event['outcome']}"}
        result["phase"] = event["outcome"]
    else:
        raise ValueError(f"unknown owner event: {kind}")
    return validate(result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["init", "apply", "show"])
    parser.add_argument("--file", type=Path, required=True)
    parser.add_argument("--owner", default=os.environ.get("WORK_GH_OWNER_ID"))
    parser.add_argument("--session", help="Exact Agent Deck owner session ID, not a title")
    parser.add_argument("--input", type=Path, help="JSON owner seed (init) or one event (apply)")
    args = parser.parse_args()
    if args.command == "show":
        print(json.dumps(load(args.file), indent=2))
        return
    require(text(args.owner) and text(args.session) and args.input is not None, "mutations require owner, session, and input")
    event = json.loads(args.input.read_text(encoding="utf-8"))
    with locked(args.file):
        if args.command == "init":
            require(not args.file.exists(), "owner state already exists; resume it, never reset budgets")
            record = new_owner(args.owner, event["batch_id"], args.session, event["chain"], event["feature_contract"])
        else:
            record = apply(load(args.file, "owner"), event, args.owner, args.session)
        save(args.file, record)
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, TypeError, KeyError) as exc:
        raise SystemExit(str(exc)) from exc
