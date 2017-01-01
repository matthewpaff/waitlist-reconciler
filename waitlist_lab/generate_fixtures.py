"""Original supplied-outcome waitlist scenarios; not real bookings."""


def request(key, correlation, party):
    return {"event": "request", "request_id": key, "correlation_id": correlation, "party_size": party}


def reconcile(correlation, confirmed):
    return {"event": "reconcile", "correlation_id": correlation, "confirmed": confirmed}


def outcome(kind, key, result):
    return {"event": kind, "request_id": key, "outcome": result}


def state(key, correlation, party, status="pending", timeouts=0):
    return {"request_id": key, "correlation_id": correlation, "party_size": party, "status": status, "timeouts": timeouts}


def make_case(index):
    key, correlation = "request-{}".format(index), "corr-{}".format(index)
    party, kind = 1 + index % 8, index % 12
    first = request(key, correlation, party)
    events = [first]
    initial = outcome("request", key, "pending")
    if kind == 0:
        events = [{"event": "timeout", "request_id": key}]
        description = "reject timeouts for unknown requests"
    elif kind == 1:
        first["party_size"] = 0
        description = "reject zero-sized waitlist parties"
    elif kind == 2:
        events.append(request(key + "-b", correlation, party))
        description = "reject correlation IDs shared by different requests"
    elif kind == 3:
        events.append(request(key, correlation, party + 1))
        description = "reject conflicting payloads for an idempotency key"
    elif kind == 4:
        events.append(reconcile(correlation, 1))
        description = "require explicit boolean reconciliation outcomes"
    elif kind == 5:
        events.append({"event": "timeout", "request_id": key})
        expected = {"outcomes": [initial, outcome("timeout", key, "pending")], "requests": [state(key, correlation, party, timeouts=1)]}
        description = "keep timed-out requests pending until reconciled"
    elif kind == 6:
        events.extend([{"event": "timeout", "request_id": key}, reconcile(correlation, True)])
        expected = {"outcomes": [initial, outcome("timeout", key, "pending"), outcome("reconcile", key, "confirmed")],
                    "requests": [state(key, correlation, party, "confirmed", 1)]}
        description = "confirm a pending request from a supplied reconciliation outcome"
    elif kind == 7:
        events.append(reconcile(correlation, False))
        expected = {"outcomes": [initial, outcome("reconcile", key, "rejected")], "requests": [state(key, correlation, party, "rejected")]}
        description = "resolve a request from a supplied rejection outcome"
    elif kind == 8:
        events.append(request(key, correlation, party))
        expected = {"outcomes": [initial, outcome("request", key, "duplicate")], "requests": [state(key, correlation, party)]}
        description = "deduplicate repeated waitlist request payloads"
    elif kind == 9:
        events.extend([reconcile(correlation, True), reconcile(correlation, True)])
        expected = {"outcomes": [initial, outcome("reconcile", key, "confirmed"), outcome("reconcile", key, "duplicate")],
                    "requests": [state(key, correlation, party, "confirmed")]}
        description = "deduplicate repeated matching reconciliation outcomes"
    elif kind == 10:
        events.extend([reconcile(correlation, True), reconcile(correlation, False)])
        description = "reject conflicting outcomes after a request is resolved"
    else:
        other, second_correlation = key + "-b", correlation + "-b"
        events.extend([request(other, second_correlation, 2), reconcile(second_correlation, True)])
        expected = {"outcomes": [initial, outcome("request", other, "pending"), outcome("reconcile", other, "confirmed")],
                    "requests": [state(key, correlation, party), state(other, second_correlation, 2, "confirmed")]}
        description = "isolate reconciliation by external correlation ID"
    case = {"id": "waitlist-{:04d}".format(index), "description": description, "input": {"events": events}}
    case.update({"expected_error": True} if kind in (0, 1, 2, 3, 4, 10) else {"expected": expected})
    return case
