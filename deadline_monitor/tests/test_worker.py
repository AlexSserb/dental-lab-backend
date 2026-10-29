from datetime import date, datetime, timezone
from unittest import TestCase

from deadline_monitor.config import ConfigurationError, Settings
from deadline_monitor.domain import OpenOrder, PendingOperation
from deadline_monitor.notifier import SnsNotifier
from deadline_monitor.worker import resolve_now, run

ENV = {
    "DATABASE_NAME": "db",
    "DATABASE_USER": "user",
    "DATABASE_PASSWORD": "secret",
    "DATABASE_HOST": "localhost",
    "ALERT_TOPIC_ARN": "arn:aws:sns:us-east-1:000000000000:alerts",
}
NOW = datetime(2026, 11, 2, 4, 0, tzinfo=timezone.utc)


class FakeRepository:
    def __init__(self, orders):
        self.orders = orders

    def fetch_open_orders(self):
        return self.orders


class FakeNotifier:
    def __init__(self):
        self.sent = []

    def send(self, subject, message):
        self.sent.append((subject, message))


class RunTest(TestCase):
    def setUp(self):
        self.settings = Settings.from_env(ENV)
        self.notifier = FakeNotifier()

    def test_sends_one_digest_for_all_risks(self):
        late = OpenOrder("11111111-aaaa", date(2026, 10, 30), 3, "Клиника №1", (PendingOperation("w", 30),))
        tight = OpenOrder("22222222-bbbb", date(2026, 11, 2), 3, "Клиника №2", (PendingOperation("w", 420),))

        summary = run(FakeRepository([late, tight]), self.notifier, self.settings, NOW)

        self.assertEqual(summary, {"checked": 2, "at_risk": 2, "notified": True})
        self.assertEqual(len(self.notifier.sent), 1)
        subject, message = self.notifier.sent[0]
        self.assertTrue(subject.isascii())
        self.assertIn("11111111", message)
        self.assertIn("Срок истёк", message)
        self.assertIn("нужно 7.0 ч, доступно 8.0 ч", message)

    def test_silent_when_everything_is_on_track(self):
        fine = OpenOrder("x", date(2026, 11, 20), 3, "Клиника", (PendingOperation("w", 30),))

        summary = run(FakeRepository([fine]), self.notifier, self.settings, NOW)

        self.assertEqual(summary, {"checked": 1, "at_risk": 0, "notified": False})
        self.assertEqual(self.notifier.sent, [])


class ResolveNowTest(TestCase):
    def test_uses_event_time(self):
        self.assertEqual(resolve_now({"time": "2026-11-02T04:00:00Z"}), NOW)

    def test_falls_back_to_clock(self):
        self.assertIsNotNone(resolve_now({}).tzinfo)
        self.assertIsNotNone(resolve_now(None).tzinfo)


class SettingsTest(TestCase):
    def test_reports_all_missing_variables(self):
        with self.assertRaisesRegex(ConfigurationError, "DATABASE_NAME.*ALERT_TOPIC_ARN"):
            Settings.from_env({"DATABASE_USER": "u", "DATABASE_PASSWORD": "p", "DATABASE_HOST": "h"})

    def test_rejects_bad_ratio(self):
        with self.assertRaises(ConfigurationError):
            Settings.from_env({**ENV, "DEADLINE_WARNING_RATIO": "1.5"})


class SnsNotifierTest(TestCase):
    def test_publishes_to_topic_and_truncates_subject(self):
        class Client:
            def publish(self, **kwargs):
                self.kwargs = kwargs
                return {"MessageId": "1"}

        client = Client()
        SnsNotifier("arn:topic", client).send("s" * 200, "тело")

        self.assertEqual(client.kwargs["TopicArn"], "arn:topic")
        self.assertEqual(len(client.kwargs["Subject"]), 99)
        self.assertEqual(client.kwargs["Message"], "тело")
