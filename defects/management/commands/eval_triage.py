"""
Run the triage eval harness against a real LLM and print the accuracy report.

    manage.py eval_triage                            # the configured AI_MODEL
    manage.py eval_triage --model qwen2.5:7b-instruct --base-url http://localhost:11434/v1

Classification accuracy (defect type, severity, both) and operation-choice accuracy are reported separately;
a case whose LLM call fails counts as a miss in both. --verbose prints every case, otherwise only the misses.
"""
from django.conf import settings

from defects.evals.runner import format_report, load_cases, run_eval

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Score the triage prompts on labeled cases (defects/evals/triage_cases.json) against a real LLM."

    def add_arguments(self, parser):
        parser.add_argument("--model", default=settings.AI_MODEL, help="Model name, as the provider accepts it")
        parser.add_argument("--base-url", default=settings.AI_BASE_URL, help="OpenAI-compatible endpoint")
        parser.add_argument("--limit", type=int, default=None, help="Run only the first N cases (smoke runs)")
        parser.add_argument("--verbose", action="store_true", help="Print every case, not only the misses")

    def handle(self, *args, **options):
        settings.AI_MODEL = options["model"]
        settings.AI_BASE_URL = options["base_url"]
        # get_client is lru_cached: clear it, or an earlier call would pin the previous endpoint/model.
        from llm.client import get_client
        get_client.cache_clear()

        cases = load_cases()
        if options["limit"]:
            cases = cases[: options["limit"]]

        self.stdout.write(f"Running {len(cases)} case(s) on {settings.AI_MODEL}...")
        results = run_eval(cases, report=self.stdout.write if options["verbose"] else self._silent_progress)
        self.stdout.write("")
        self.stdout.write(format_report(settings.AI_MODEL, results))

    def _silent_progress(self, line: str) -> None:
        """Show only the misses while the run is in progress; the report at the end has the totals."""
        if " miss" in line or "failed" in line:
            self.stdout.write(line)
