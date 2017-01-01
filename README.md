# Waitlist Reconciler

Replay mock waitlist requests, timeout ambiguity, idempotency keys, and supplied reconciliation outcomes.

Uses Python 3.10+ and its standard library only. No package installation, virtual
environment, external server, Redis, Celery, or network access is required.

## Run

```console
python -m waitlist_lab --help
python -m waitlist_lab examples/sample.json
python -m waitlist_lab --check-fixtures fixtures/cases.jsonl
python generate_fixtures.py --count 20
python -m unittest discover -s tests -v
```

Run from this directory. The optional path defaults to `-`, which reads JSON from
stdin. Output is JSON or a fixture-check summary. Exit codes are 0 success,
1 file failure, and 2 invalid input. Examples and fixtures contain generated data.

Input requires exactly an events list of at most 500 entries. request events supply request_id, correlation_id, and party_size from 1–20. timeout events supply request_id and leave unresolved requests pending. reconcile events supply a known correlation_id and an explicit boolean confirmed outcome. Matching repeated requests and resolutions are deduplicated; conflicting idempotency payloads or resolved outcomes are rejected. Correlation IDs cannot be reused by different requests. Results are sorted by request ID. Outcomes are supplied mock data, not verified provider responses. No HTTP request, booking, persistence, real waitlist, or automatic timeout clock is involved.

## Learning focus

The modeled 2017 waitlist-provider learning themes: pending states, external correlation IDs, timeout ambiguity, and reconciliation from the roadmap's P05 sandbox. This is an independent concept exercise based on the modeled
roadmap. It makes no claim to be employer-owned or period-authentic production code.

## Structure

- `waitlist_lab/core.py`: validated parsing, storage, or state transitions.
- `waitlist_lab/cli.py`: JSON command interface.
- `waitlist_lab/generate_fixtures.py`: original deterministic validation cases.
- `waitlist_lab/fixture_check.py`: expected-output/error checks.
- `fixtures/cases.jsonl`: 367 generated cases, with explicit descriptions.
- `tests/`: independently selected boundaries and the complete corpus check.

Branches `feature/core`, `feature/cli`, `data/fixtures`, and `docs/usage` retain
snapshots; `main` contains the complete tool. Dates and provenance are also recorded
in TIMELINE.json. Many data cases share a scenario; they are not separate features.

Keep changes focused, use actual dates for new work, and add a regression test
for changed behavior. Licensed under [MIT](LICENSE).

[History and provenance](HISTORY.md).
