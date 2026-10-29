"""Delivery of alerts."""

import logging
from typing import Protocol

logger = logging.getLogger(__name__)

# SNS accepts only printable ASCII in a subject, shorter than 100 characters.
MAX_SUBJECT_LENGTH = 99


class Notifier(Protocol):
    def send(self, subject: str, message: str) -> None: ...


class SnsNotifier:
    def __init__(self, topic_arn: str, client=None):
        self._topic_arn = topic_arn
        self._client = client

    def send(self, subject: str, message: str) -> None:
        response = self._get_client().publish(
            TopicArn=self._topic_arn,
            Subject=subject[:MAX_SUBJECT_LENGTH],
            Message=message,
        )
        logger.info("Alert published, message id %s", response.get("MessageId"))

    def _get_client(self):
        if self._client is None:
            # Imported lazily: the assessment logic and its tests do not need the AWS SDK.
            import boto3

            self._client = boto3.client("sns")
        return self._client
