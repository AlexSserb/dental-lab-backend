"""
Print (or email) the AI workflow health report.

    manage.py monitoring_digest             # print for the last 24 hours
    manage.py monitoring_digest --hours 48 --email
"""
from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.utils import timezone

from ops.digest import format_digest
from ops.monitoring import llm_stats, triage_health


class Command(BaseCommand):
    help = "Collect LLM and defect-triage health into a digest; print it and optionally email EMAIL_ADMIN."

    def add_arguments(self, parser):
        parser.add_argument("--hours", type=int, default=24, help="Window for LLM stats (default 24)")
        parser.add_argument("--email", action="store_true", help="Also send the digest to EMAIL_ADMIN")

    def handle(self, *args, **options):
        stats = llm_stats(options["hours"])
        health = triage_health()
        subject, message = format_digest(stats, health, options["hours"], timezone.now())

        self.stdout.write(message)
        if options["email"]:
            try:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.EMAIL_ADMIN],
                    fail_silently=False,
                )
                self.stdout.write("Digest sent to EMAIL_ADMIN.")
            except Exception as exc:
                self.stderr.write(f"Failed to send the digest email: {exc}")
                raise SystemExit(1)
