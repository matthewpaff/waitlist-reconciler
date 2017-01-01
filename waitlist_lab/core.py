"""Replay supplied booking outcomes; timeout alone never confirms a request."""
import re


def token(value, label):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", value):
        raise ValueError(label + " must use 1–80 letters, digits, underscores, or hyphens")
    return value


def fields(value, expected):
    if not isinstance(value, dict) or set(value) != expected:
        raise ValueError("Event requires exactly: " + ", ".join(sorted(expected)))


def reconcile_waitlist(data):
    if not isinstance(data, dict) or set(data) != {"events"} or not isinstance(data["events"], list) or len(data["events"]) > 500:
        raise ValueError("Supply exactly events, containing at most 500 entries")
    requests, correlations, outcomes = {}, {}, []
    for event in data["events"]:
        if not isinstance(event, dict):
            raise ValueError("Event must be an object")
        kind = event.get("event")
        if kind == "request":
            fields(event, {"event", "request_id", "correlation_id", "party_size"})
            key = token(event["request_id"], "request_id")
            correlation = token(event["correlation_id"], "correlation_id")
            party = event["party_size"]
            if type(party) is not int or not 1 <= party <= 20:
                raise ValueError("party_size must be an integer from 1 to 20")
            if key in requests:
                previous = requests[key]
                if previous["correlation_id"] != correlation or previous["party_size"] != party:
                    raise ValueError("Repeated request ID has conflicting data")
                outcome = "duplicate"
            else:
                if correlation in correlations:
                    raise ValueError("Correlation ID is already assigned to another request")
                requests[key] = {"request_id": key, "correlation_id": correlation, "party_size": party,
                                 "status": "pending", "timeouts": 0}
                correlations[correlation] = key
                outcome = "pending"
        elif kind == "timeout":
            fields(event, {"event", "request_id"})
            key = token(event["request_id"], "request_id")
            if key not in requests:
                raise ValueError("Cannot time out an unknown request")
            row = requests[key]
            if row["status"] == "pending":
                row["timeouts"] += 1
                outcome = "pending"
            else:
                outcome = "already_resolved"
        elif kind == "reconcile":
            fields(event, {"event", "correlation_id", "confirmed"})
            correlation = token(event["correlation_id"], "correlation_id")
            if type(event["confirmed"]) is not bool or correlation not in correlations:
                raise ValueError("Reconciliation needs a known correlation ID and a boolean confirmed outcome")
            key = correlations[correlation]
            row = requests[key]
            target = "confirmed" if event["confirmed"] else "rejected"
            if row["status"] == "pending":
                row["status"], outcome = target, target
            elif row["status"] == target:
                outcome = "duplicate"
            else:
                raise ValueError("Reconciliation conflicts with an already resolved outcome")
        else:
            raise ValueError("Unknown waitlist event")
        outcomes.append({"event": kind, "request_id": key, "outcome": outcome})
    return {"outcomes": outcomes, "requests": [requests[key] for key in sorted(requests)]}
