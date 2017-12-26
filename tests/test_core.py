from copy import deepcopy
from pathlib import Path
import unittest

from waitlist_lab.core import reconcile_waitlist
from waitlist_lab.fixture_check import check


def request(key="a", correlation="corr-a", party=2):
    return {"event": "request", "request_id": key, "correlation_id": correlation, "party_size": party}


class WaitlistTests(unittest.TestCase):
    def test_timeout_does_not_confirm_and_input_is_preserved(self):
        data = {"events": [request(), {"event": "timeout", "request_id": "a"}]}
        original = deepcopy(data)
        result = reconcile_waitlist(data)
        self.assertEqual(result["requests"][0]["status"], "pending")
        self.assertEqual(result["requests"][0]["timeouts"], 1)
        self.assertEqual(data, original)

    def test_correlation_resolves_the_correct_request(self):
        result = reconcile_waitlist({"events": [request("b", "corr-b"), request(), {"event": "reconcile", "correlation_id": "corr-b", "confirmed": True}]})
        self.assertEqual([(row["request_id"], row["status"]) for row in result["requests"]], [("a", "pending"), ("b", "confirmed")])

    def test_repeated_requests_and_outcomes_do_not_reset_state(self):
        confirm = {"event": "reconcile", "correlation_id": "corr-a", "confirmed": True}
        result = reconcile_waitlist({"events": [request(), confirm, request(), confirm]})
        self.assertEqual([row["outcome"] for row in result["outcomes"]], ["pending", "confirmed", "duplicate", "duplicate"])
        self.assertEqual(result["requests"][0]["status"], "confirmed")

    def test_conflicting_keys_outcomes_and_boolean_party_are_rejected(self):
        for events in ([request(), request(party=3)], [request(party=True)],
                       [request(), {"event": "reconcile", "correlation_id": "corr-a", "confirmed": True}, {"event": "reconcile", "correlation_id": "corr-a", "confirmed": False}]):
            with self.subTest(events=events), self.assertRaises(ValueError):
                reconcile_waitlist({"events": events})

    def test_complete_fixture_corpus(self):
        self.assertGreaterEqual(check(Path(__file__).resolve().parents[1] / "fixtures/cases.jsonl", reconcile_waitlist), 350)


if __name__ == "__main__":
    unittest.main()
